from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.draft import Draft
from backend.models.published_post import PublishedPost

router = APIRouter()


@router.get("/events")
async def get_calendar_events(
    month: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get calendar events for a given month (YYYY-MM format)."""
    if month:
        try:
            year, mon = map(int, month.split("-"))
        except (ValueError, AttributeError):
            year, mon = datetime.utcnow().year, datetime.utcnow().month
    else:
        year, mon = datetime.utcnow().year, datetime.utcnow().month

    start = datetime(year, mon, 1)
    if mon == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, mon + 1, 1)

    events = []

    # Published posts
    result = await db.execute(
        select(PublishedPost).where(
            PublishedPost.published_at >= start,
            PublishedPost.published_at < end,
        )
    )
    for post in result.scalars().all():
        draft = await db.get(Draft, post.draft_id)
        events.append({
            "id": f"pub-{post.id}",
            "title": draft.title if draft else "Untitled",
            "date": post.published_at.strftime("%Y-%m-%d"),
            "type": "published",
            "platform": "instagram",
            "post_url": post.post_url,
        })

    # Scheduled drafts
    result = await db.execute(
        select(Draft).where(
            Draft.status == "scheduled",
            Draft.scheduled_at >= start,
            Draft.scheduled_at < end,
        )
    )
    for draft in result.scalars().all():
        events.append({
            "id": f"draft-{draft.id}",
            "title": draft.title,
            "date": draft.scheduled_at.strftime("%Y-%m-%d"),
            "type": "scheduled",
            "platform": "instagram",
            "post_url": None,
        })

    return {"month": f"{year:04d}-{mon:02d}", "events": events}
