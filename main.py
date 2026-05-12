import base64
import json
import logging

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-ai")


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/incoming-call")
async def incoming_call(request: Request) -> Response:
    host = request.headers.get("x-forwarded-host") or request.url.hostname
    stream_url = f"wss://{host}/ws/audio"
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
            message = json.loads(raw_message)
            event = message.get("event")

            if event == "start":
                stream_sid = message.get("start", {}).get("streamSid")
                logger.info("Stream started: %s", stream_sid)
            elif event == "media":
                payload = message.get("media", {}).get("payload", "")
                audio_chunk = base64.b64decode(payload) if payload else b""
                logger.info("Received audio chunk: %d bytes", len(audio_chunk))
            elif event == "stop":
                logger.info("Stream stopped")
                break
            else:
                logger.debug("Unhandled event type: %s", event)
    except WebSocketDisconnect:
        logger.info("Twilio media stream disconnected")
