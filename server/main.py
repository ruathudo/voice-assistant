import os
import logging


from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

# Import backend modules
from .audio_utils import save_audio_file
from .openai_services import speech_to_text, generate_text, text_to_speech
from .agent import VoiceAssistantAgent
from .db import SessionLocal, Conversation
from .schemas import AudioUploadResponse, ChatHistoryResponse, ChatHistoryItem
from .websocket_manager import WebSocketManager

from dotenv import load_dotenv
load_dotenv()


app = FastAPI()
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
logging.basicConfig(level=LOGGING_LEVEL)

# Initialize agent and websocket manager
agent = VoiceAssistantAgent()
ws_manager = WebSocketManager()

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


# Upload audio and start conversation
@app.post("/api/audio", response_model=AudioUploadResponse)
async def upload_audio(file: UploadFile):
    # Save audio file
    audio_path = save_audio_file(file)
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    # Speech to text
    user_text = speech_to_text(audio_bytes)
    # Agent generates response
    response_text = agent.process(user_text)
    # Text to speech
    response_audio = text_to_speech(response_text)
    # Save to DB
    from datetime import datetime
    db = SessionLocal()
    conv = Conversation(user_input=user_text, agent_response=response_text, timestamp=datetime.utcnow())
    db.add(conv)
    db.commit()
    db.refresh(conv)
    conversation_id = str(conv.id)
    db.close()
    return {"conversation_id": conversation_id}


# Get chat history
@app.get("/api/history/{conversation_id}", response_model=ChatHistoryResponse)
async def get_history(conversation_id: str):
    db = SessionLocal()
    conv = db.query(Conversation).filter(Conversation.id == int(conversation_id)).first()
    db.close()
    if not conv:
        return {"conversation_id": conversation_id, "history": []}
    history = [ChatHistoryItem(user_input=conv.user_input, agent_response=conv.agent_response, timestamp=str(conv.timestamp))]
    return {"conversation_id": conversation_id, "history": history}


# WebSocket for streaming text/audio
@app.websocket("/ws/conversation/{conversation_id}")
async def conversation_ws(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Use agent to process incoming text
            response_text = agent.process(data)
            await ws_manager.send_text(websocket, f'{ {"event": "text", "data": response_text} }')
            # Generate audio and stream (stub)
            response_audio = text_to_speech(response_text)
            await websocket.send_bytes(response_audio)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
