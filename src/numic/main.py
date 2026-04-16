"""FastAPI application entrypoint."""

from fastapi import FastAPI

from numic.api.v1.demo_router import demo_router
from numic.api.v1.router import api_router

app = FastAPI(title="numic", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
