"""Demo database: engine, sessions and table creation (no migrations; the demo holds synthetic data only)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from numic.demo.models import DemoBase


class DemoDatabase:
    def __init__(self, url: str, echo: bool = False) -> None:
        self.engine = create_async_engine(url, echo=echo)
        self.sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(DemoBase.metadata.create_all)

    async def dispose(self) -> None:
        await self.engine.dispose()


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    db: DemoDatabase | None = getattr(request.app.state, "demo_db", None)
    if db is None:
        raise HTTPException(status_code=503, detail="The demo database is not available")
    async with db.sessionmaker() as session:
        yield session


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    """SQLite returns naive datetimes; everything is stored in UTC."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
