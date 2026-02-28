import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.routers import drafts, ai, settings, instagram, publish, calendar


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Srija Social Media Assistant", lifespan=lifespan)


@app.post("/api/shutdown")
async def shutdown():
    """Gracefully shut down the server by closing the entire console window."""

    async def _kill():
        await asyncio.sleep(0.5)
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            else:
                os._exit(0)
        else:
            import signal
            os.kill(os.getpid(), signal.SIGTERM)

    asyncio.get_event_loop().create_task(_kill())
    return JSONResponse({"message": "Server shutting down..."})


# API routers
app.include_router(drafts.router, prefix="/api/drafts", tags=["drafts"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(instagram.router, prefix="/api/auth/instagram", tags=["instagram"])
app.include_router(publish.router, prefix="/api/publish", tags=["publish"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])

# Serve frontend static files
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")
