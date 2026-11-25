"""
FastAPI application factory and instance for Project 07 Red Ingestion API.
"""

import mimetypes
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.config import IngestionSettings, settings
from api.dependencies import get_settings
from api.routes import analytics_router, events_router, health_router

# Prevent Windows registry permission errors in restricted environments
mimetypes._mimetypes_read_windows_registry = None

"""
FastAPI application factory and instance for Project 07 Red Ingestion API.
"""

import asyncio
from contextlib import asynccontextmanager
import mimetypes
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.config import IngestionSettings, settings
from api.dependencies import get_settings
from api.routes import analytics_router, events_router, health_router

# Prevent Windows registry permission errors in restricted environments
mimetypes._mimetypes_read_windows_registry = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"


def create_app(app_settings: IngestionSettings = settings) -> FastAPI:
    """Creates and configures a FastAPI application instance."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        current_settings = app.dependency_overrides.get(get_settings, lambda: app_settings)()
        watchdog_task = None
        if current_settings.WATCHDOG_AUTO_EVALUATE:
            async def watchdog_worker():
                from api.dependencies import get_watchdog_engine
                engine = get_watchdog_engine()
                while True:
                    try:
                        await asyncio.sleep(current_settings.WATCHDOG_INTERVAL_SEC)
                        engine.check_watchdogs()
                    except asyncio.CancelledError:
                        break
                    except Exception:
                        pass

            watchdog_task = asyncio.create_task(watchdog_worker())

        yield

        if watchdog_task and not watchdog_task.done():
            watchdog_task.cancel()
            try:
                await watchdog_task
            except asyncio.CancelledError:
                pass

    app = FastAPI(
        title=app_settings.API_TITLE,
        version=app_settings.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Allow custom app_settings to take effect in dependency injection
    app.dependency_overrides[get_settings] = lambda: app_settings

    # Mount API routers under /api/v1
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(events_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")

    # Mount static assets
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="frontend-assets")

    def _serve_spa():
        if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
            return HTMLResponse(content=(FRONTEND_DIST_DIR / "index.html").read_text(encoding="utf-8"))
        if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
            return HTMLResponse(content=(STATIC_DIR / "index.html").read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Project 07 Red Ingestion API</h1><p>Running. Access /docs.</p>")

    @app.get("/", include_in_schema=False)
    @app.get("/dashboard", include_in_schema=False)
    def serve_dashboard():
        return _serve_spa()

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa_route(full_path: str):
        # Exclude API endpoints and docs from SPA fallback
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")
        # Check if requesting a direct file in frontend dist (like favicon.svg, vite.svg)
        if FRONTEND_DIST_DIR.exists():
            target_file = FRONTEND_DIST_DIR / full_path
            if target_file.is_file():
                return FileResponse(str(target_file))
        return _serve_spa()

    return app


app = create_app()
