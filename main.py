import base64
import json
import logging
import os
import re

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-ai")
HOST_PATTERN = re.compile(r"^[A-Za-z0-9.-]+(?::\d{1,5})?$")


def _resolve_stream_url(request: Request) -> str:
    base_url = os.getenv("PUBLIC_BASE_URL")
    if base_url:
        normalized = base_url.rstrip("/")
        if normalized.startswith("https://"):
            return f"wss://{normalized.removeprefix('https://')}/ws/audio"
        if normalized.startswith("wss://"):
            return f"{normalized}/ws/audio"
        logger.warning("PUBLIC_BASE_URL must start with https:// or wss://, falling back to request host")

    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_host and HOST_PATTERN.fullmatch(forwarded_host):
        return f"wss://{forwarded_host}/ws/audio"

    host = request.url.hostname or "localhost"
    return f"wss://{host}/ws/audio"


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/incoming-call")
async def incoming_call(request: Request) -> Response:
    stream_url = _resolve_stream_url(request)
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Connect>"
        f'<Stream url="{stream_url}" />'
        "</Connect>"
        "</Response>"
    )
    logger.info("Generated TwiML stream URL: %s", stream_url)
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("Twilio media stream connected")

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                logger.warning("Received malformed JSON from websocket")
                continue
            event = message.get("event")

            if event == "start":
                stream_sid = message.get("start", {}).get("streamSid")
                logger.info("Stream started: %s", stream_sid)
            elif event == "media":
                payload = message.get("media", {}).get("payload", "")
                audio_chunk = base64.b64decode(payload) if payload else b""
                logger.debug("Received audio chunk: %d bytes", len(audio_chunk))
            elif event == "stop":
                logger.info("Stream stopped")
                break
            else:
                logger.debug("Unhandled event type: %s", event)
    except WebSocketDisconnect:
        logger.info("Twilio media stream disconnected")
