import os
import logging
import base64
import json

import soundfile as sf
import numpy as np


from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agents.voice import AudioInput

# Import backend modules
# from .audio_utils import save_audio_file
# from .openai_services import speech_to_text, generate_text, text_to_speech
# from .agent import VoiceAssistantAgent
# from .db import SessionLocal, Conversation
# from .schemas import AudioUploadResponse, ChatHistoryResponse, ChatHistoryItem

from .agent import run_agent


from dotenv import load_dotenv
load_dotenv()


app = FastAPI()
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
logging.basicConfig(level=LOGGING_LEVEL)

# Initialize agent and websocket manager
# agent = VoiceAssistantAgent()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/ping")
async def ping():
    return {"status": "ok"}


@app.post("/voice")
async def voice_chat(file: UploadFile = File(media_type="audio/wav")) -> StreamingResponse:
    """
    Receive a recorded wav file, pass it to the VoicePipeline, 
    and return the agent’s audio response as streaming output.
    """
    # Ensure file is wav
    if not file.filename.endswith(".wav"):
        return {"error": "Only .wav files are supported"}

    # Read file into memory
    wav_bytes = await file.read()

    audio_generator = run_agent(wav_bytes)
    return StreamingResponse(audio_generator, media_type="audio/wav")

@app.websocket("/ws/voice")
async def websocket_voice(ws: WebSocket):
    await ws.accept()
    buffer = []

    try:
        while True:
            msg = await ws.receive_bytes()

            if msg == b"__END__":
                # Finalize full input once client signals end of utterance
                if not buffer:
                    await ws.send_text(json.dumps({"type": "error", "msg": "no audio received"}))
                    continue

                full_pcm = np.concatenate(buffer).astype(np.float32)
                # audio_input = AudioInput(buffer=full_pcm, frame_rate=16000)

                # Save to .wav for debugging
                sf.write("user_input.wav", full_pcm, 16000, subtype="PCM_16")

                await ws.send_text(json.dumps({
                    "type": "text",
                    "data": "Received audio input, processing..."
                }))

                async for chunk in run_agent(full_pcm):
                    await ws.send_bytes(chunk)

                await ws.send_text(json.dumps({
                    "type": "end",
                    "data": "Response complete."
                }))

                # Reset buffer for next utterance
                # buffer.clear()
            else:
                # Accumulate PCM float32 chunks
                pcm = np.frombuffer(msg, dtype=np.float32)
                buffer.append(pcm)

    except WebSocketDisconnect:
        print("Client disconnected")

# Upload audio and start conversation
# @app.post("/api/audio", response_model=AudioUploadResponse)
# async def upload_audio(file: UploadFile):
#     # Save audio file
#     audio_path = save_audio_file(file)
#     with open(audio_path, "rb") as f:
#         audio_bytes = f.read()
#     # Speech to text
#     user_text = speech_to_text(audio_bytes)
#     # Agent generates response
#     response_text = agent.process(user_text)
#     # Text to speech
#     response_audio = text_to_speech(response_text)
#     # Save to DB
#     from datetime import datetime
#     db = SessionLocal()
#     conv = Conversation(user_input=user_text, agent_response=response_text, timestamp=datetime.utcnow())
#     db.add(conv)
#     db.commit()
#     db.refresh(conv)
#     conversation_id = str(conv.id)
#     db.close()
#     return {"conversation_id": conversation_id}


# Get chat history
# @app.get("/api/history/{conversation_id}", response_model=ChatHistoryResponse)
# async def get_history(conversation_id: str):
#     db = SessionLocal()
#     conv = db.query(Conversation).filter(Conversation.id == int(conversation_id)).first()
#     db.close()
#     if not conv:
#         return {"conversation_id": conversation_id, "history": []}
#     history = [ChatHistoryItem(user_input=conv.user_input, agent_response=conv.agent_response, timestamp=str(conv.timestamp))]
#     return {"conversation_id": conversation_id, "history": history}


# WebSocket for streaming text/audio
# @app.websocket("/ws/conversation/{conversation_id}")
# async def conversation_ws(websocket: WebSocket, conversation_id: str):
#     await websocket.accept()
#     ws_manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             # Use agent to process incoming text
#             response_text = agent.process(data)
#             await ws_manager.send_text(websocket, f'{ {"event": "text", "data": response_text} }')
#             # Generate audio and stream (stub)
#             response_audio = text_to_speech(response_text)
#             await websocket.send_bytes(response_audio)
#     except WebSocketDisconnect:
#         ws_manager.disconnect(websocket)

