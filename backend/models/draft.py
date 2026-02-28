from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    content_type: Mapped[str] = mapped_column(String(50))  # lifestyle, travel, food, etc.
    body: Mapped[str] = mapped_column(Text, default="")  # Single body (Instagram only)
    status: Mapped[str] = mapped_column(String(20), default="idea")  # idea, draft, ready, scheduled, published
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    images: Mapped[list["DraftImage"]] = relationship(
        "DraftImage", back_populates="draft", cascade="all, delete-orphan",
        order_by="DraftImage.sort_order"
    )


from backend.models.image import DraftImage  # noqa: E402, F811
