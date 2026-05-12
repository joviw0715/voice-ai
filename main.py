import base64
import binascii
import json
import logging
import os
import re

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-ai")
HOST_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def _is_valid_host(host: str) -> bool:
    hostname, separator, port = host.rpartition(":")
    if separator and port:
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            return False
    else:
        hostname = host

    if not hostname:
        return False
    if hostname == "localhost":
        return True
    if ".." in hostname:
        return False

    return all(HOST_LABEL_PATTERN.fullmatch(label) for label in hostname.split("."))


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
    if forwarded_host and _is_valid_host(forwarded_host):
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
                try:
                    audio_chunk = base64.b64decode(payload, validate=True) if payload else b""
                except (binascii.Error, ValueError):
                    logger.warning("Received invalid base64 audio payload")
                    continue
                logger.debug("Received audio chunk: %d bytes", len(audio_chunk))
            elif event == "stop":
                logger.info("Stream stopped")
                break
            else:
                logger.debug("Unhandled event type: %s", event)
    except WebSocketDisconnect:
        logger.info("Twilio media stream disconnected")
