"""Async SQLAlchemy session factory."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from numic.core.config import get_settings

_settings = get_settings()
engine = create_async_engine(_settings.database_url, echo=_settings.database_echo)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
