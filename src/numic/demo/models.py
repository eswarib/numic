"""Demo tables: sandboxes, babies and scans. Portable types so the demo runs on PostgreSQL or SQLite.

Seed rows have ``sandbox_id = NULL`` and are shared and read-only. Rows a visitor adds carry that
visitor's sandbox ID, including scans added to a seed baby.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class DemoBase(DeclarativeBase):
    pass


class DemoSandbox(DemoBase):
    __tablename__ = "demo_sandboxes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    """Random token; the browser sends it in the ``X-Demo-Sandbox`` header."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class DemoBaby(DemoBase):
    __tablename__ = "demo_babies"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    """Patient ID shown to visitors: ``DEMO-0003`` for seed babies, ``DEMO-7K3Q`` for added ones."""
    sandbox_id: Mapped[str | None] = mapped_column(
        ForeignKey("demo_sandboxes.id", ondelete="CASCADE"), index=True
    )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    ga_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    ga_days: Mapped[int] = mapped_column(Integer, nullable=False)
    seed_born_days_ago: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DemoScan(DemoBase):
    __tablename__ = "demo_scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    baby_id: Mapped[str] = mapped_column(
        ForeignKey("demo_babies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sandbox_id: Mapped[str | None] = mapped_column(
        ForeignKey("demo_sandboxes.id", ondelete="CASCADE"), index=True
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vi_left_mm: Mapped[float] = mapped_column(Float, nullable=False)
    vi_right_mm: Mapped[float] = mapped_column(Float, nullable=False)
    ahw_mm: Mapped[float] = mapped_column(Float, nullable=False)
    tod_mm: Mapped[float] = mapped_column(Float, nullable=False)
    clinical_concern: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
