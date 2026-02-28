import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.models.social_account import SocialAccount
from backend.services.encryption import encrypt_token
from backend.services.instagram import InstagramService

router = APIRouter()


def _get_ig_service() -> InstagramService:
    if not settings.instagram_app_id or not settings.instagram_app_secret:
        raise HTTPException(status_code=400, detail="Instagram App ID and Secret not configured. Set them in Settings.")
    return InstagramService(
        app_id=settings.instagram_app_id,
        app_secret=settings.instagram_app_secret,
        redirect_uri=settings.instagram_redirect_uri,
    )


@router.get("/login")
async def get_login_url():
    """Return Instagram OAuth authorization URL."""
    svc = _get_ig_service()
    state = secrets.token_urlsafe(16)
    url = svc.get_auth_url(state=state)
    return {"url": url, "state": state}


@router.get("/callback")
async def oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle Instagram OAuth callback — exchange code for token and store."""
    svc = _get_ig_service()
    try:
        result = await svc.exchange_code(code)
    except ValueError as e:
        return _oauth_error_html(str(e))

    # Upsert account
    existing = await db.execute(
        select(SocialAccount).where(SocialAccount.platform == "instagram")
    )
    account = existing.scalar_one_or_none()

    encrypted = encrypt_token(result["access_token"])

    if account:
        account.platform_user_id = result["user_id"]
        account.display_name = result["username"]
        account.access_token = encrypted
        account.token_expires_at = result["expires_at"]
        account.scopes = "instagram_business_basic,instagram_business_content_publish"
    else:
        account = SocialAccount(
            platform="instagram",
            platform_user_id=result["user_id"],
            display_name=result["username"],
            access_token=encrypted,
            token_expires_at=result["expires_at"],
            scopes="instagram_business_basic,instagram_business_content_publish",
        )
        db.add(account)

    await db.commit()

    # Return HTML that closes popup and notifies parent
    return _oauth_success_html(result["username"])


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    """Check if Instagram is connected."""
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.platform == "instagram")
    )
    account = result.scalar_one_or_none()
    if not account:
        return {"connected": False}
    return {
        "connected": True,
        "username": account.display_name,
        "user_id": account.platform_user_id,
        "expires_at": account.token_expires_at.isoformat() if account.token_expires_at else None,
    }


@router.delete("/disconnect")
async def disconnect(db: AsyncSession = Depends(get_db)):
    """Remove Instagram connection."""
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.platform == "instagram")
    )
    account = result.scalar_one_or_none()
    if account:
        await db.delete(account)
        await db.commit()
    return {"message": "Instagram disconnected"}


def _oauth_success_html(username: str) -> "HTMLResponse":
    from fastapi.responses import HTMLResponse
    return HTMLResponse(f"""
    <html><body><script>
        window.opener && window.opener.postMessage({{
            type: 'oauth-success',
            platform: 'instagram',
            name: '{username}'
        }}, '*');
        window.close();
    </script><p>Connected as @{username}! You can close this window.</p></body></html>
    """)


def _oauth_error_html(error: str) -> "HTMLResponse":
    from fastapi.responses import HTMLResponse
    return HTMLResponse(f"""
    <html><body><script>
        window.opener && window.opener.postMessage({{
            type: 'oauth-error',
            platform: 'instagram',
            error: '{error}'
        }}, '*');
    </script><p>Error: {error}</p><p>Close this window and try again.</p></body></html>
    """)
