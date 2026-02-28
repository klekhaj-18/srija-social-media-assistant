from typing import Literal

from pydantic import BaseModel, field_validator


VALID_TONES = {"casual", "aesthetic", "witty", "inspirational", "informative", "professional", "friendly", "exciting"}


class AIGenerateRequest(BaseModel):
    content_type: Literal[
        "lifestyle", "travel", "food", "fitness", "tech",
        "personal_update", "quote", "promotion",
    ]
    context: str = ""
    tone: str = "casual"  # comma-separated: "casual,aesthetic"
    additional_instructions: str = ""
    conversation_history: list[dict] = []

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        tones = [t.strip() for t in v.split(",") if t.strip()]
        invalid = [t for t in tones if t not in VALID_TONES]
        if invalid:
            raise ValueError(f"Invalid tone(s): {', '.join(invalid)}")
        return v


class AIGenerateResponse(BaseModel):
    text: str
    provider: str
    model: str
    tokens_used: int | None = None
