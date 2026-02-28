# Srija Social Media Assistant

Personal Instagram posting assistant with AI-powered caption generation.

## Quick Start

1. Copy `.env.example` to `.env`
2. Double-click `launch.bat` (or run `python run.py`)
3. Open http://localhost:8600

## Setup

### Prerequisites
- Python 3.11+
- Instagram Creator account
- Meta Developer App (for Instagram API)
- Google Cloud service account (for image hosting)
- Anthropic API key (for AI captions)

### Configuration
All settings can be configured through the web UI (Settings page) or by editing `.env`:

- **ANTHROPIC_API_KEY** — Your Anthropic API key
- **INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET** — From Meta Developer dashboard
- **GOOGLE_DRIVE_CREDENTIALS_FILE** — Path to service account JSON
- **GOOGLE_DRIVE_FOLDER_ID** — Google Drive folder for temp image uploads
- **TOKEN_ENCRYPTION_KEY** — Auto-generated via Settings page

### Android App
Open the `android/` folder in Android Studio to build the APK.
Configure the backend server URL in the app settings (Menu > Server Settings).

## Tech Stack
- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **Frontend**: Alpine.js + Tailwind CSS (no build step)
- **AI**: Anthropic Claude (Haiku)
- **Android**: WebView wrapper
