"""
app/models/chat.py
──────────────────
Pydantic schemas for chat request/response.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class ChatMode(str, Enum):
    HR = "hr"
    TECHNICAL = "technical"
    SUMMARY = "summary"


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    mode: ChatMode = Field(default=ChatMode.HR, description="Response mode")
    session_id: Optional[str] = Field(None, description="Optional session tracking ID")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Tell me about your most impressive project",
                "mode": "hr",
                "session_id": "sess_abc123"
            }
        }


class ChatResponse(BaseModel):
    response: str
    mode: str
    session_id: Optional[str] = None
    context_sources: Optional[list[str]] = None  # Which chunks were used


class StreamEvent(BaseModel):
    type: Literal["token", "done", "error"]
    data: str
