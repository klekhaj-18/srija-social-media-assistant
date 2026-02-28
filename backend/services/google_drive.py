from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class GoogleDriveService:
    def __init__(self, credentials_file: str, folder_id: str):
        self.folder_id = folder_id
        creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES
        )
        self.service = build("drive", "v3", credentials=creds)

    def upload_image(self, file_path: str, filename: str | None = None) -> dict:
        """Upload an image to Google Drive and make it publicly accessible.

        Returns dict with 'file_id' and 'public_url'.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        mime_type = mime_map.get(path.suffix.lower(), "image/jpeg")

        file_metadata = {
            "name": filename or path.name,
            "parents": [self.folder_id],
        }
        media = MediaFileUpload(str(path), mimetype=mime_type)

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()

        file_id = file["id"]

        # Make publicly accessible
        self.service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

        public_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        return {
            "file_id": file_id,
            "public_url": public_url,
        }

    def delete_file(self, file_id: str):
        """Delete a file from Google Drive (cleanup after publishing)."""
        try:
            self.service.files().delete(fileId=file_id).execute()
        except Exception:
            pass  # Best-effort cleanup
