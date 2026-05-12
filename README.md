# voice-ai
with inbound/outbound call with Twilio, free local LLM that powers  assistant's intelligence, reasoning, and conversation abilities., transcriber with azure for speech-to-text transcriber that converts caller speech into text for the LLM and minimax for text-to-speech voice assistant uses to speak.

# Voice AI Backend (Step 1)

## Run locally
pip install -r requirements.txt  
uvicorn main:app --reload

## Deploy
Deploy to Zeabur using GitHub integration.

## Twilio Setup
Set webhook:
POST /incoming-call

## Goal
Receive real-time audio from Twilio via WebSocket.
