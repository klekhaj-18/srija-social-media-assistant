import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from pathlib import Path

import httpx

router = APIRouter()

ENV_PATH = Path(".env")


class AIKeysUpdate(BaseModel):
    anthropic_api_key: str | None = None


class AIKeysResponse(BaseModel):
    anthropic_configured: bool


def _read_env() -> dict[str, str]:
    """Read .env file into a dict."""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def _write_env(env: dict[str, str]):
    """Write dict back to .env, preserving comments and structure."""
    lines = []
    if ENV_PATH.exists():
        existing_lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    else:
        existing_lines = []

    written_keys = set()
    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _, _ = stripped.partition("=")
            key = key.strip()
            if key in env:
                lines.append(f"{key}={env[key]}")
                written_keys.add(key)
            else:
                lines.append(line)
        else:
            lines.append(line)

    for key, value in env.items():
        if key not in written_keys:
            lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


@router.get("/ai-keys", response_model=AIKeysResponse)
async def get_ai_keys():
    env = _read_env()
    return AIKeysResponse(
        anthropic_configured=bool(env.get("ANTHROPIC_API_KEY", "")),
    )


@router.put("/ai-keys")
async def update_ai_keys(data: AIKeysUpdate):
    env = _read_env()
    if data.anthropic_api_key is not None:
        env["ANTHROPIC_API_KEY"] = data.anthropic_api_key
    _write_env(env)
    # Reload settings
    from backend.config import Settings
    import backend.config as cfg
    cfg.settings = Settings()
    return {"message": "API key updated. Restart the server for full effect."}


class OAuthCredsUpdate(BaseModel):
    instagram_app_id: str | None = None
    instagram_app_secret: str | None = None
    token_encryption_key: str | None = None


class OAuthCredsResponse(BaseModel):
    instagram_configured: bool
    encryption_key_configured: bool


@router.get("/oauth-creds", response_model=OAuthCredsResponse)
async def get_oauth_creds():
    env = _read_env()
    return OAuthCredsResponse(
        instagram_configured=bool(env.get("INSTAGRAM_APP_ID", "")) and bool(env.get("INSTAGRAM_APP_SECRET", "")),
        encryption_key_configured=bool(env.get("TOKEN_ENCRYPTION_KEY", "")),
    )


@router.put("/oauth-creds")
async def update_oauth_creds(data: OAuthCredsUpdate):
    env = _read_env()
    if data.instagram_app_id is not None:
        env["INSTAGRAM_APP_ID"] = data.instagram_app_id
    if data.instagram_app_secret is not None:
        env["INSTAGRAM_APP_SECRET"] = data.instagram_app_secret
    if data.token_encryption_key is not None:
        env["TOKEN_ENCRYPTION_KEY"] = data.token_encryption_key
    _write_env(env)
    from backend.config import Settings
    import backend.config as cfg
    cfg.settings = Settings()
    return {"message": "Credentials updated."}


class DriveCredsUpdate(BaseModel):
    google_drive_credentials_file: str | None = None
    google_drive_folder_id: str | None = None


class DriveCredsResponse(BaseModel):
    drive_configured: bool


@router.get("/drive-creds", response_model=DriveCredsResponse)
async def get_drive_creds():
    env = _read_env()
    return DriveCredsResponse(
        drive_configured=bool(env.get("GOOGLE_DRIVE_CREDENTIALS_FILE", "")) and bool(env.get("GOOGLE_DRIVE_FOLDER_ID", "")),
    )


@router.put("/drive-creds")
async def update_drive_creds(data: DriveCredsUpdate):
    env = _read_env()
    if data.google_drive_credentials_file is not None:
        env["GOOGLE_DRIVE_CREDENTIALS_FILE"] = data.google_drive_credentials_file
    if data.google_drive_folder_id is not None:
        env["GOOGLE_DRIVE_FOLDER_ID"] = data.google_drive_folder_id
    _write_env(env)
    from backend.config import Settings
    import backend.config as cfg
    cfg.settings = Settings()
    return {"message": "Google Drive credentials updated."}


@router.post("/generate-encryption-key")
async def generate_encryption_key():
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    env = _read_env()
    env["TOKEN_ENCRYPTION_KEY"] = key
    _write_env(env)
    from backend.config import Settings
    import backend.config as cfg
    cfg.settings = Settings()
    return {"message": "Encryption key generated and saved.", "configured": True}


class TestKeyRequest(BaseModel):
    provider: str  # "anthropic"
    api_key: str


@router.post("/test-ai-key")
async def test_ai_key(data: TestKeyRequest):
    """Test an AI API key with a minimal request."""
    try:
        if data.provider == "anthropic":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": data.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hi"}],
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    return {"success": True, "message": "Anthropic key is valid!"}
                error = resp.json().get("error", {})
                msg = error.get("message", resp.text)
                return {"success": False, "message": msg}
        else:
            return {"success": False, "message": f"Unknown provider: {data.provider}"}

    except httpx.TimeoutException:
        return {"success": False, "message": "Request timed out"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/export-backup")
async def export_backup():
    env = _read_env()
    if not env:
        raise HTTPException(status_code=404, detail="No settings found to export")

    backup = {
        "version": 1,
        "exported_at": datetime.utcnow().isoformat(),
        "settings": env,
    }
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"srija-settings-backup-{date_str}.json"

    return Response(
        content=json.dumps(backup, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import-backup")
async def import_backup(file: UploadFile = File(...)):
    if file.content_type and file.content_type not in ("application/json", "text/json"):
        raise HTTPException(status_code=400, detail="File must be a JSON file")

    content = await file.read()
    if len(content) > 1 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 1 MB.")

    try:
        backup = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    if not isinstance(backup, dict) or "settings" not in backup:
        raise HTTPException(status_code=400, detail="Invalid backup format")

    settings_data = backup["settings"]
    if not isinstance(settings_data, dict):
        raise HTTPException(status_code=400, detail="Invalid backup format")

    env = _read_env()
    imported_count = 0
    for key, value in settings_data.items():
        if isinstance(value, str):
            env[key] = value
            imported_count += 1
    _write_env(env)

    from backend.config import Settings
    import backend.config as cfg
    cfg.settings = Settings()

    return {"message": f"Imported {imported_count} settings successfully.", "imported_count": imported_count}
