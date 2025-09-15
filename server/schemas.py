# schemas.py
"""
Pydantic models for request and response validation.
"""

from pydantic import BaseModel
from typing import List

class AudioUploadResponse(BaseModel):
    conversation_id: str

class ChatHistoryItem(BaseModel):
    user_input: str
    agent_response: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    conversation_id: str
    history: List[ChatHistoryItem]
