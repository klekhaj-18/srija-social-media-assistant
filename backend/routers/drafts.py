import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database import get_db
from backend.models.draft import Draft
from backend.models.image import DraftImage
from backend.schemas.draft import DraftCreate, DraftUpdate, DraftResponse, DraftImageResponse

router = APIRouter()


@router.get("/", response_model=list[DraftResponse])
async def list_drafts(
    status: str | None = None,
    content_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Draft).options(selectinload(Draft.images)).order_by(desc(Draft.updated_at))
    if status:
        query = query.where(Draft.status == status)
    if content_type:
        query = query.where(Draft.content_type == content_type)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=DraftResponse, status_code=201)
async def create_draft(data: DraftCreate, db: AsyncSession = Depends(get_db)):
    draft = Draft(**data.model_dump())
    db.add(draft)
    await db.commit()
    await db.refresh(draft, ["images"])
    return draft


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Draft).options(selectinload(Draft.images)).where(Draft.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(draft_id: int, data: DraftUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Draft).options(selectinload(Draft.images)).where(Draft.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)
    await db.commit()
    await db.refresh(draft, ["images"])
    return draft


@router.delete("/{draft_id}", status_code=204)
async def delete_draft(draft_id: int, db: AsyncSession = Depends(get_db)):
    draft = await db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    await db.delete(draft)
    await db.commit()


@router.post("/{draft_id}/images", response_model=DraftImageResponse, status_code=201)
async def upload_image(
    draft_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    draft = await db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Use JPEG, PNG, WebP, or GIF.",
        )

    MAX_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / filename

    file_path.write_bytes(content)

    result = await db.execute(
        select(DraftImage).where(DraftImage.draft_id == draft_id)
    )
    existing = result.scalars().all()
    sort_order = len(existing)

    image = DraftImage(
        draft_id=draft_id,
        file_path=f"images/{filename}",
        sort_order=sort_order,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


@router.delete("/{draft_id}/images/{image_id}", status_code=204)
async def delete_image(draft_id: int, image_id: int, db: AsyncSession = Depends(get_db)):
    image = await db.get(DraftImage, image_id)
    if not image or image.draft_id != draft_id:
        raise HTTPException(status_code=404, detail="Image not found")
    file_path = Path(settings.upload_dir).parent / image.file_path
    if file_path.exists():
        file_path.unlink()
    await db.delete(image)
    await db.commit()
