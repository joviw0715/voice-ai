from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import Response
import json
import base64

app = FastAPI()

@app.post("/incoming-call")
async def incoming_call(request: Request):
    twiml = """
    <Response>
        <Connect>
            <Stream url="wss://voice-ai.zeabur.app/ws/audio" />
        </Connect>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws/audio")
async def websocket_audio(ws: WebSocket):
    await ws.accept()
    print("✅ WebSocket connected")

    try:
        while True:
            data = await ws.receive_text()
            message = json.loads(data)

            event_type = message.get("event")

            if event_type == "start":
                print("📞 Call started")
                print(message["start"])

            elif event_type == "media":
                payload = message["media"]["payload"]
                audio = base64.b64decode(payload)
                print(f"🎤 Received audio: {len(audio)} bytes")

            elif event_type == "stop":
                print("❌ Call ended")
                break

    except Exception as e:
        print("Error:", e)
