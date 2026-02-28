import asyncio
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx

from backend.services.encryption import encrypt_token, decrypt_token

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.instagram.com/{GRAPH_API_VERSION}"


class InstagramService:
    def __init__(self, app_id: str, app_secret: str, redirect_uri: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self, state: str = "") -> str:
        """Generate Instagram OAuth authorization URL."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": "instagram_business_basic,instagram_business_content_publish",
            "response_type": "code",
        }
        if state:
            params["state"] = state
        return f"https://api.instagram.com/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for short-lived token, then upgrade to long-lived."""
        async with httpx.AsyncClient() as client:
            # Step 1: Exchange code for short-lived token
            resp = await client.post(
                "https://api.instagram.com/oauth/access_token",
                data={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                raise ValueError(f"Token exchange failed: {resp.text}")

            data = resp.json()
            short_token = data["access_token"]
            user_id = str(data["user_id"])

            # Step 2: Exchange for long-lived token (60 days)
            resp = await client.get(
                "https://graph.instagram.com/access_token",
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": self.app_secret,
                    "access_token": short_token,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                raise ValueError(f"Long-lived token exchange failed: {resp.text}")

            ll_data = resp.json()
            long_token = ll_data["access_token"]
            expires_in = ll_data.get("expires_in", 5184000)  # Default 60 days

            # Step 3: Get user profile
            resp = await client.get(
                f"https://graph.instagram.com/me",
                params={
                    "fields": "user_id,username",
                    "access_token": long_token,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                raise ValueError(f"Profile fetch failed: {resp.text}")

            profile = resp.json()

            return {
                "user_id": user_id,
                "username": profile.get("username", ""),
                "access_token": long_token,
                "expires_at": datetime.utcnow() + timedelta(seconds=expires_in),
            }

    async def refresh_token(self, encrypted_token: str) -> dict:
        """Refresh a long-lived token before it expires."""
        token = decrypt_token(encrypted_token)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://graph.instagram.com/refresh_access_token",
                params={
                    "grant_type": "ig_refresh_token",
                    "access_token": token,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                raise ValueError(f"Token refresh failed: {resp.text}")

            data = resp.json()
            return {
                "access_token": data["access_token"],
                "expires_at": datetime.utcnow() + timedelta(seconds=data.get("expires_in", 5184000)),
            }

    async def publish_post(self, encrypted_token: str, ig_user_id: str, caption: str, image_url: str) -> dict:
        """Publish a single image post to Instagram using the two-step container process."""
        token = decrypt_token(encrypted_token)
        async with httpx.AsyncClient() as client:
            # Step 1: Create media container
            resp = await client.post(
                f"{GRAPH_BASE}/{ig_user_id}/media",
                data={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": token,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                raise ValueError(f"Container creation failed: {resp.text}")

            container_id = resp.json()["id"]

            # Step 2: Wait for processing (poll status)
            for _ in range(12):  # Max 60 seconds
                await asyncio.sleep(5)
                status_resp = await client.get(
                    f"{GRAPH_BASE}/{container_id}",
                    params={
                        "fields": "status_code",
                        "access_token": token,
                    },
                    timeout=15,
                )
                if status_resp.status_code == 200:
                    status = status_resp.json().get("status_code")
                    if status == "FINISHED":
                        break
                    elif status == "ERROR":
                        raise ValueError("Instagram media processing failed")

            # Step 3: Publish the container
            resp = await client.post(
                f"{GRAPH_BASE}/{ig_user_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": token,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                raise ValueError(f"Publishing failed: {resp.text}")

            media_id = resp.json()["id"]

            # Get permalink
            permalink = ""
            perm_resp = await client.get(
                f"{GRAPH_BASE}/{media_id}",
                params={
                    "fields": "permalink",
                    "access_token": token,
                },
                timeout=15,
            )
            if perm_resp.status_code == 200:
                permalink = perm_resp.json().get("permalink", "")

            return {
                "platform_post_id": media_id,
                "post_url": permalink,
            }

    async def publish_carousel(self, encrypted_token: str, ig_user_id: str, caption: str, image_urls: list[str]) -> dict:
        """Publish a carousel (multi-image) post."""
        token = decrypt_token(encrypted_token)
        async with httpx.AsyncClient() as client:
            # Step 1: Create child containers
            child_ids = []
            for url in image_urls:
                resp = await client.post(
                    f"{GRAPH_BASE}/{ig_user_id}/media",
                    data={
                        "image_url": url,
                        "is_carousel_item": "true",
                        "access_token": token,
                    },
                    timeout=30,
                )
                if resp.status_code != 200:
                    raise ValueError(f"Child container creation failed: {resp.text}")
                child_ids.append(resp.json()["id"])

            # Wait for all children to process
            await asyncio.sleep(10)

            # Step 2: Create carousel container
            resp = await client.post(
                f"{GRAPH_BASE}/{ig_user_id}/media",
                data={
                    "media_type": "CAROUSEL",
                    "caption": caption,
                    "children": ",".join(child_ids),
                    "access_token": token,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                raise ValueError(f"Carousel container creation failed: {resp.text}")

            container_id = resp.json()["id"]

            # Wait for carousel processing
            for _ in range(12):
                await asyncio.sleep(5)
                status_resp = await client.get(
                    f"{GRAPH_BASE}/{container_id}",
                    params={"fields": "status_code", "access_token": token},
                    timeout=15,
                )
                if status_resp.status_code == 200:
                    status = status_resp.json().get("status_code")
                    if status == "FINISHED":
                        break
                    elif status == "ERROR":
                        raise ValueError("Carousel processing failed")

            # Step 3: Publish
            resp = await client.post(
                f"{GRAPH_BASE}/{ig_user_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": token,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                raise ValueError(f"Carousel publishing failed: {resp.text}")

            media_id = resp.json()["id"]

            permalink = ""
            perm_resp = await client.get(
                f"{GRAPH_BASE}/{media_id}",
                params={"fields": "permalink", "access_token": token},
                timeout=15,
            )
            if perm_resp.status_code == 200:
                permalink = perm_resp.json().get("permalink", "")

            return {
                "platform_post_id": media_id,
                "post_url": permalink,
            }
