from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class PublishedPost(Base):
    __tablename__ = "published_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"))
    platform: Mapped[str] = mapped_column(String(20))  # "instagram"
    platform_post_id: Mapped[str] = mapped_column(String(200))  # IG media ID
    post_url: Mapped[str] = mapped_column(Text, default="")  # Permalink
    account_id: Mapped[int] = mapped_column(ForeignKey("social_accounts.id"))
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
