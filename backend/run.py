import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import asyncio
import uvicorn
from backend.app.core.config import settings

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    print(f"Starting {settings.APP_NAME} on http://{settings.APP_HOST}:{settings.APP_PORT} ...")
    backend_dir = os.path.join(PROJECT_ROOT, "backend")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
        reload_dirs=[backend_dir],
        reload_excludes=["*.db*", "data/*", "browser_profile/*"],
        loop="asyncio",
    )
