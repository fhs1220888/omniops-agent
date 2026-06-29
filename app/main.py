"""FastAPI entrypoint for OmniOps Agent."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.approvals import router as approvals_router
from app.api.demo import router as demo_router
from app.api.harness import router as harness_router
from app.api.incidents import router as incidents_router
from app.api.runtime import router as runtime_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.include_router(incidents_router, prefix=settings.api_prefix)
    app.include_router(approvals_router, prefix=settings.api_prefix)
    app.include_router(demo_router, prefix=settings.api_prefix)
    app.include_router(harness_router, prefix=settings.api_prefix)
    app.include_router(runtime_router, prefix=settings.api_prefix)
    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    return app


app = create_app()
