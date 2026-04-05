from fastapi import APIRouter

from app.models.schemas import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AIChatRequest,
    AIChatResponse,
)
from app.services.ai_service import analyze_video, chat, health_check

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/analyze", response_model=AIAnalysisResponse)
async def ai_analyze(request: AIAnalysisRequest):
    """Analyze video metadata and recommend optimal compression settings.

    Uses the local LLM (Qwen2.5-Coder 7B) when available, falls back to
    rule-based recommendations otherwise.
    """
    return await analyze_video(request)


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(request: AIChatRequest):
    """Chat with the AI assistant about video compression topics.

    Optionally include video metadata as context for more relevant answers.
    """
    return await chat(request)


@router.get("/health")
async def ai_health():
    """Check the AI service health and connectivity."""
    return await health_check()
