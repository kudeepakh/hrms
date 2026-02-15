"""Chat route — authenticated endpoint for the HRMS agent."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.agent.orchestrator import run_agent
from app.auth.dependencies import get_current_user
from app.models.schemas import ChatRequest, ChatResponse
from app.models.user import User

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: User = Depends(get_current_user)):
    """Send a message to the HRMS agent. Requires authentication."""
    reply = await run_agent(
        user_message=request.message,
        session_id=request.session_id or user.email,
        user=user,
    )
    return ChatResponse(reply=reply)
