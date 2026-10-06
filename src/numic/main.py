"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from numic.api.v1.demo_router import demo_router
from numic.api.v1.router import api_router

_CLINICAL_DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "web" / "clinical-demo"

app = FastAPI(title="numic", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")

if _CLINICAL_DEMO_DIR.is_dir():
    app.mount(
        "/clinical-demo",
        StaticFiles(directory=str(_CLINICAL_DEMO_DIR), html=True),
        name="clinical_demo",
    )


@app.get("/health")
def health():
    return {"status": "ok"}
