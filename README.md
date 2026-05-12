# voice-ai

Minimal FastAPI backend for receiving real-time Twilio call audio over WebSocket.

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Optional (recommended for production): set a stable public URL used in TwiML:
   ```bash
   export PUBLIC_BASE_URL=https://your-domain.com
   ```

## Twilio webhook setup

1. Expose your local server using an HTTPS tunnel (for example ngrok).
2. In Twilio Console, set your incoming phone number Voice webhook URL to:
   - `https://<your-domain>/incoming-call`
   - Method: `POST`
3. When a call arrives, Twilio receives TwiML from `/incoming-call` and connects audio to:
   - `wss://<your-domain>/ws/audio`

## Deploy to Zeabur

1. Push this repository to GitHub.
2. In Zeabur, create a new project and import this repository.
3. Zeabur will use `Procfile`:
   - `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Configure your Twilio webhook to:
   - `https://<your-zeabur-domain>/incoming-call`
