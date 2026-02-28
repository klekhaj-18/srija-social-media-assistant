"""Srija Social Media Assistant — Launcher

Double-click or run `python run.py` to start the app.
Opens your browser to http://localhost:8600 automatically.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def ensure_venv():
    """Create virtual environment if it doesn't exist and install dependencies."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])

    # Determine pip path
    if sys.platform == "win32":
        pip = venv_path / "Scripts" / "pip.exe"
        python = venv_path / "Scripts" / "python.exe"
    else:
        pip = venv_path / "bin" / "pip"
        python = venv_path / "bin" / "python"

    # Install dependencies if needed
    requirements = Path("requirements.txt")
    if requirements.exists():
        print("Installing dependencies...")
        subprocess.check_call([str(pip), "install", "-r", "requirements.txt", "-q"])

    return str(python)


def main():
    python = ensure_venv()
    host = "127.0.0.1"
    port = 8600
    url = f"http://{host}:{port}"

    print(f"\nStarting Srija Social Media Assistant...")
    print(f"Opening {url} in your browser...\n")

    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start uvicorn
    subprocess.call([
        python, "-m", "uvicorn",
        "backend.main:app",
        "--host", host,
        "--port", str(port),
        "--reload",
    ])


if __name__ == "__main__":
    main()
