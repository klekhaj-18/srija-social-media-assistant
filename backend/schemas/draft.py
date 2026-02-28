from datetime import datetime

from pydantic import BaseModel


class DraftImageResponse(BaseModel):
    id: int
    file_path: str
    sort_order: int
    alt_text: str | None = None

    model_config = {"from_attributes": True}


class DraftCreate(BaseModel):
    title: str
    content_type: str = "lifestyle"
    body: str = ""
    status: str = "idea"
    scheduled_at: datetime | None = None


class DraftUpdate(BaseModel):
    title: str | None = None
    content_type: str | None = None
    body: str | None = None
    status: str | None = None
    scheduled_at: datetime | None = None


class DraftResponse(BaseModel):
    id: int
    title: str
    content_type: str
    body: str
    status: str
    scheduled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    images: list[DraftImageResponse] = []

    model_config = {"from_attributes": True}
