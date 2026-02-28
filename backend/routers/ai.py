from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.ai.claude import ClaudeClient
from backend.schemas.ai import AIGenerateRequest, AIGenerateResponse

router = APIRouter()


def _get_client() -> ClaudeClient:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="Anthropic API key not configured. Set it in Settings.")
    return ClaudeClient(api_key=settings.anthropic_api_key)


@router.post("/generate", response_model=AIGenerateResponse)
async def generate_content(data: AIGenerateRequest):
    client = _get_client()
    try:
        result = await client.generate(
            content_type=data.content_type,
            context=data.context,
            tone=data.tone,
            additional_instructions=data.additional_instructions,
            conversation_history=data.conversation_history or None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")

    return AIGenerateResponse(**result)


@router.get("/status")
async def ai_status():
    """Check if AI is configured."""
    return {"configured": bool(settings.anthropic_api_key)}
