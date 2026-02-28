from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database import get_db
from backend.models.published_post import PublishedPost
from backend.models.social_account import SocialAccount
from backend.models.draft import Draft
from backend.services.instagram import InstagramService
from backend.services.google_drive import GoogleDriveService

router = APIRouter()


class PublishRequest(BaseModel):
    draft_id: int


class PublishedPostResponse(BaseModel):
    id: int
    draft_id: int
    platform: str
    platform_post_id: str
    post_url: str
    published_at: str
    is_scheduled: bool
    scheduled_for: str | None = None
    draft_title: str | None = None

    class Config:
        from_attributes = True


@router.post("/publish")
async def publish(data: PublishRequest, db: AsyncSession = Depends(get_db)):
    """Publish a draft to Instagram."""
    # Load draft with images
    result = await db.execute(
        select(Draft).where(Draft.id == data.draft_id).options(selectinload(Draft.images))
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if not draft.body:
        raise HTTPException(status_code=400, detail="Draft has no content")

    # Get Instagram account
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.platform == "instagram")
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=400, detail="No Instagram account connected. Connect in Settings.")

    # Check for images — Instagram requires at least one image
    if not draft.images:
        raise HTTPException(status_code=400, detail="Instagram posts require at least one image. Upload an image to this draft first.")

    # Upload images to Google Drive for public URLs
    drive_file_ids = []
    image_urls = []

    if not settings.google_drive_credentials_file or not settings.google_drive_folder_id:
        raise HTTPException(
            status_code=400,
            detail="Google Drive not configured. Set credentials file and folder ID in Settings.",
        )

    try:
        drive = GoogleDriveService(
            credentials_file=settings.google_drive_credentials_file,
            folder_id=settings.google_drive_folder_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive setup failed: {e}")

    try:
        for img in draft.images:
            local_path = Path("backend/static") / img.file_path
            if not local_path.exists():
                continue
            upload_result = drive.upload_image(str(local_path))
            drive_file_ids.append(upload_result["file_id"])
            image_urls.append(upload_result["public_url"])

        if not image_urls:
            raise HTTPException(status_code=400, detail="No valid images found to upload")

        # Publish to Instagram
        ig_service = InstagramService(
            app_id=settings.instagram_app_id,
            app_secret=settings.instagram_app_secret,
            redirect_uri=settings.instagram_redirect_uri,
        )

        if len(image_urls) == 1:
            pub_result = await ig_service.publish_post(
                encrypted_token=account.access_token,
                ig_user_id=account.platform_user_id,
                caption=draft.body,
                image_url=image_urls[0],
            )
        else:
            pub_result = await ig_service.publish_carousel(
                encrypted_token=account.access_token,
                ig_user_id=account.platform_user_id,
                caption=draft.body,
                image_urls=image_urls,
            )

        # Store published post record
        published = PublishedPost(
            draft_id=draft.id,
            platform="instagram",
            platform_post_id=pub_result["platform_post_id"],
            post_url=pub_result.get("post_url", ""),
            account_id=account.id,
        )
        db.add(published)

        # Update draft status
        draft.status = "published"
        await db.commit()

        return {
            "success": True,
            "post_id": pub_result["platform_post_id"],
            "post_url": pub_result.get("post_url", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publishing failed: {e}")
    finally:
        # Cleanup Drive files
        if drive_file_ids:
            try:
                drive = GoogleDriveService(
                    credentials_file=settings.google_drive_credentials_file,
                    folder_id=settings.google_drive_folder_id,
                )
                for fid in drive_file_ids:
                    drive.delete_file(fid)
            except Exception:
                pass


@router.get("/history", response_model=list[PublishedPostResponse])
async def get_published_history(db: AsyncSession = Depends(get_db)):
    """Get published post history."""
    query = select(PublishedPost).order_by(PublishedPost.published_at.desc())
    result = await db.execute(query)
    posts = result.scalars().all()

    response = []
    for post in posts:
        draft = await db.get(Draft, post.draft_id)
        response.append(PublishedPostResponse(
            id=post.id,
            draft_id=post.draft_id,
            platform=post.platform,
            platform_post_id=post.platform_post_id,
            post_url=post.post_url,
            published_at=post.published_at.isoformat(),
            is_scheduled=post.is_scheduled,
            scheduled_for=post.scheduled_for.isoformat() if post.scheduled_for else None,
            draft_title=draft.title if draft else None,
        ))

    return response


@router.delete("/history/{post_id}", status_code=204)
async def delete_published_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await db.get(PublishedPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Published post not found")
    await db.delete(post)
    await db.commit()


@router.delete("/history", status_code=204)
async def clear_published_history(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(PublishedPost))
    await db.commit()
