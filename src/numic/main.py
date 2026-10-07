"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from numic.api.v1.demo_router import demo_router
from numic.api.v1.router import api_router
from numic.core.config import get_settings
from numic.demo.db import DemoDatabase
from numic.demo.router import sandbox_router
from numic.demo.seed import Maintenance

log = logging.getLogger(__name__)


def _clinical_demo_dir() -> Path | None:
    """Source checkout first, then the working directory (non-editable installs, e.g. on Railway)."""
    for base in (Path(__file__).resolve().parent.parent.parent, Path.cwd()):
        candidate = base / "web" / "clinical-demo"
        if candidate.is_dir():
            return candidate
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    maintenance = None
    if settings.demo_enabled:
        db = DemoDatabase(settings.database_url, settings.database_echo)
        await db.create_tables()
        maintenance = Maintenance(
            db,
            settings.scan_day_timezone,
            settings.demo_sandbox_ttl_days,
            settings.demo_maintenance_interval_seconds,
        )
        await maintenance.run_once()  # seed babies dated relative to today before serving
        maintenance.start()
        app.state.demo_db = db
    yield
    if maintenance is not None:
        await maintenance.stop()
        await app.state.demo_db.dispose()
        app.state.demo_db = None


app = FastAPI(title="numic", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")
app.include_router(sandbox_router, prefix="/api/v1")

_demo_dir = _clinical_demo_dir()
if _demo_dir is not None:
    app.mount(
        "/clinical-demo",
        StaticFiles(directory=str(_demo_dir), html=True),
        name="clinical_demo",
    )

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/clinical-demo/")


@app.get("/health")
def health():
    return {"status": "ok"}
