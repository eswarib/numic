"""Seed babies (dates stored as offsets from today) and the daily clean-up job."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from numic.demo.db import DemoDatabase, as_utc, utcnow
from numic.demo.models import DemoBaby, DemoSandbox, DemoScan

log = logging.getLogger(__name__)

SEED_PATH = Path(__file__).resolve().parent / "seed_babies.json"


@dataclass(frozen=True, slots=True)
class SeedScan:
    day: int
    time: time
    vi_left: float
    vi_right: float
    ahw: float
    tod: float
    concern: str


@dataclass(frozen=True, slots=True)
class SeedBaby:
    id: str
    story: str
    born_days_ago: int
    ga_weeks: int
    ga_days: int
    scans: tuple[SeedScan, ...]


@lru_cache
def load_seed(path: Path = SEED_PATH) -> tuple[SeedBaby, ...]:
    raw = json.loads(path.read_text())
    out = []
    for b in raw["babies"]:
        scans = tuple(
            SeedScan(
                day=s["day"],
                time=time.fromisoformat(s["time"]),
                vi_left=s["vi_left"],
                vi_right=s["vi_right"],
                ahw=s["ahw"],
                tod=s["tod"],
                concern=s["concern"],
            )
            for s in b["scans"]
        )
        if any(s.day >= b["born_days_ago"] for s in scans):
            raise ValueError(f"{b['id']}: every seed scan must be before today")
        out.append(
            SeedBaby(b["id"], b["story"], b["born_days_ago"], b["ga_weeks"], b["ga_days"], scans)
        )
    return tuple(out)


def seed_stories() -> dict[str, str]:
    return {b.id: b.story for b in load_seed()}


def local_today(tz: str) -> date:
    return utcnow().astimezone(ZoneInfo(tz)).date()


def seed_scan_id(baby_id: str, index: int) -> str:
    return f"{baby_id}-S{index + 1}"


async def apply_seed(session: AsyncSession, today: date, tz: str) -> None:
    """Insert or re-date the seed babies so that ages are realistic on ``today``.

    Visitor scans on a seed baby move by the same number of days, so their chart keeps its shape.
    """
    zone = ZoneInfo(tz)
    now = utcnow()
    seed = load_seed()
    for sb in seed:
        dob = today - timedelta(days=sb.born_days_ago)
        baby = await session.get(DemoBaby, sb.id)
        if baby is None:
            baby = DemoBaby(id=sb.id, sandbox_id=None, created_at=now)
            session.add(baby)
            shift = timedelta(0)
        else:
            shift = dob - baby.date_of_birth
        baby.date_of_birth = dob
        baby.ga_weeks, baby.ga_days = sb.ga_weeks, sb.ga_days
        baby.seed_born_days_ago = sb.born_days_ago

        for i, s in enumerate(sb.scans):
            sid = seed_scan_id(sb.id, i)
            scan = await session.get(DemoScan, sid)
            if scan is None:
                scan = DemoScan(id=sid, baby_id=sb.id, sandbox_id=None, created_at=now)
                session.add(scan)
            scan.measured_at = datetime.combine(dob + timedelta(days=s.day), s.time, zone)
            scan.vi_left_mm, scan.vi_right_mm = s.vi_left, s.vi_right
            scan.ahw_mm, scan.tod_mm, scan.clinical_concern = s.ahw, s.tod, s.concern
        keep = [seed_scan_id(sb.id, i) for i in range(len(sb.scans))]
        await session.execute(
            delete(DemoScan).where(
                DemoScan.baby_id == sb.id, DemoScan.sandbox_id.is_(None), DemoScan.id.not_in(keep)
            )
        )

        if shift:
            visitor_scans = await session.scalars(
                select(DemoScan).where(DemoScan.baby_id == sb.id, DemoScan.sandbox_id.is_not(None))
            )
            for v in visitor_scans:
                v.measured_at = as_utc(v.measured_at) + shift
    await session.commit()


async def delete_sandbox_rows(session: AsyncSession, sandbox_ids: list[str]) -> None:
    """Delete a sandbox's scans and babies explicitly (SQLite does not enforce cascades by default)."""
    if not sandbox_ids:
        return
    own_babies = select(DemoBaby.id).where(DemoBaby.sandbox_id.in_(sandbox_ids))
    await session.execute(
        delete(DemoScan).where(
            DemoScan.sandbox_id.in_(sandbox_ids) | DemoScan.baby_id.in_(own_babies)
        )
    )
    await session.execute(delete(DemoBaby).where(DemoBaby.sandbox_id.in_(sandbox_ids)))


async def delete_expired_sandboxes(session: AsyncSession, ttl_days: int) -> int:
    cutoff = utcnow() - timedelta(days=ttl_days)
    expired = list(await session.scalars(select(DemoSandbox.id).where(DemoSandbox.last_seen_at < cutoff)))
    await delete_sandbox_rows(session, expired)
    await session.execute(delete(DemoSandbox).where(DemoSandbox.id.in_(expired)))
    await session.commit()
    return len(expired)


class Maintenance:
    """Start-up and periodic job: re-date the seed when the day changes, delete inactive sandboxes."""

    def __init__(self, db: DemoDatabase, tz: str, ttl_days: int, interval_seconds: int) -> None:
        self.db, self.tz, self.ttl_days, self.interval = db, tz, ttl_days, interval_seconds
        self.seeded_for: date | None = None
        self._task: asyncio.Task | None = None

    async def run_once(self) -> None:
        today = local_today(self.tz)
        async with self.db.sessionmaker() as session:
            if self.seeded_for != today:
                await apply_seed(session, today, self.tz)
                self.seeded_for = today
            removed = await delete_expired_sandboxes(session, self.ttl_days)
        if removed:
            log.info("demo clean-up removed %d inactive sandboxes", removed)

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self.interval)
            try:
                await self.run_once()
            except Exception:  # keep the loop alive; the next run retries
                log.exception("demo maintenance failed")

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
