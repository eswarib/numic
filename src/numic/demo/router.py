"""Public demo API: seed babies plus a private sandbox per visitor (``X-Demo-Sandbox`` header).

A header is used instead of a cookie so the demo also works inside an embedded frame. Every query
returns seed rows plus the current sandbox's rows, never another sandbox's.
"""

from __future__ import annotations

import re
import secrets
import time
import uuid
from collections import defaultdict, deque
from datetime import timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from numic.core.config import Settings, get_settings
from numic.demo.db import as_utc, get_session, utcnow
from numic.demo.models import DemoBaby, DemoSandbox, DemoScan
from numic.demo.schemas import BabyCreate, BabyDetail, BabyList, ScanCreate
from numic.demo.seed import delete_sandbox_rows, local_today, seed_stories
from numic.demo.service import baby_detail, rule_set_info, score_scans, summarise
from numic.scoring.rules import get_rules

SANDBOX_HEADER = "X-Demo-Sandbox"
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{20,64}$")
_ID_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # no 0/O/1/I, so never clashes with DEMO-00NN seeds

sandbox_router = APIRouter(prefix="/demo", tags=["demo"])


# --- sandbox and limits -------------------------------------------------------------------------


async def current_sandbox(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> DemoSandbox:
    """The visitor's sandbox; a missing or unknown token gets a new one, never another visitor's."""
    token = request.headers.get(SANDBOX_HEADER, "")
    now = utcnow()
    sandbox = await session.get(DemoSandbox, token) if _TOKEN_RE.match(token) else None
    if sandbox is None:
        sandbox = DemoSandbox(id=secrets.token_urlsafe(24), created_at=now, last_seen_at=now)
        session.add(sandbox)
    elif now - as_utc(sandbox.last_seen_at) > timedelta(minutes=5):
        sandbox.last_seen_at = now
    await session.commit()
    response.headers[SANDBOX_HEADER] = sandbox.id
    return sandbox


class WriteRateLimiter:
    """Sliding one-minute window per client IP (in memory; the demo runs as one process)."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, ip: str, limit: int) -> None:
        now = time.monotonic()
        hits = self._hits[ip]
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= limit:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit reached: at most {limit} changes per minute. Please wait a moment.",
            )
        hits.append(now)


write_limiter = WriteRateLimiter()


def limit_writes(request: Request, settings: Settings = Depends(get_settings)) -> None:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    write_limiter.check(ip, settings.demo_writes_per_minute)


# --- helpers ------------------------------------------------------------------------------------


def _visible(model, sandbox: DemoSandbox):
    return or_(model.sandbox_id.is_(None), model.sandbox_id == sandbox.id)


async def _get_baby(session: AsyncSession, sandbox: DemoSandbox, baby_id: str) -> DemoBaby:
    baby = await session.get(DemoBaby, baby_id)
    if baby is None or baby.sandbox_id not in (None, sandbox.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No baby {baby_id}")
    return baby


async def _visible_scans(session: AsyncSession, sandbox: DemoSandbox, baby_id: str) -> list[DemoScan]:
    rows = await session.scalars(
        select(DemoScan).where(DemoScan.baby_id == baby_id, _visible(DemoScan, sandbox))
    )
    return list(rows)


async def _detail(session: AsyncSession, sandbox: DemoSandbox, baby: DemoBaby, settings: Settings) -> BabyDetail:
    scans = await _visible_scans(session, sandbox, baby.id)
    return baby_detail(
        baby,
        scans,
        get_rules(),
        settings.scan_day_timezone,
        seed_stories().get(baby.id),
        settings.demo_max_scans_per_baby,
    )


async def _new_baby_id(session: AsyncSession) -> str:
    for _ in range(20):
        candidate = "DEMO-" + "".join(secrets.choice(_ID_ALPHABET) for _ in range(4))
        if await session.get(DemoBaby, candidate) is None:
            return candidate
    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not allocate a patient ID")


def _read_only() -> HTTPException:
    return HTTPException(
        status.HTTP_403_FORBIDDEN,
        detail="Pre-loaded demo babies and their scans are shared and cannot be changed. "
        "You can add your own scans to them.",
    )


# --- endpoints ----------------------------------------------------------------------------------


@sandbox_router.get("/babies", response_model=BabyList)
async def list_babies(
    sandbox: DemoSandbox = Depends(current_sandbox),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BabyList:
    rules = get_rules()
    babies = list(await session.scalars(select(DemoBaby).where(_visible(DemoBaby, sandbox))))
    scans = list(await session.scalars(select(DemoScan).where(_visible(DemoScan, sandbox))))
    by_baby: dict[str, list[DemoScan]] = defaultdict(list)
    for s in scans:
        by_baby[s.baby_id].append(s)
    stories = seed_stories()
    summaries = [
        summarise(b, score_scans(b, by_baby[b.id], rules, settings.scan_day_timezone), stories.get(b.id))
        for b in babies
    ]
    summaries.sort(key=lambda b: (b.read_only, b.id))  # visitor's own babies first, then seed
    return BabyList(
        babies=summaries,
        sandbox_baby_count=sum(1 for b in babies if b.sandbox_id == sandbox.id),
        max_babies=settings.demo_max_babies_per_sandbox,
        rule_set=rule_set_info(rules),
    )


@sandbox_router.get("/babies/{baby_id}", response_model=BabyDetail)
async def get_baby(
    baby_id: str,
    sandbox: DemoSandbox = Depends(current_sandbox),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BabyDetail:
    baby = await _get_baby(session, sandbox, baby_id)
    return await _detail(session, sandbox, baby, settings)


@sandbox_router.post(
    "/babies",
    response_model=BabyDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_writes)],
)
async def add_baby(
    body: BabyCreate,
    sandbox: DemoSandbox = Depends(current_sandbox),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BabyDetail:
    today = local_today(settings.scan_day_timezone)
    if body.date_of_birth > today:
        raise HTTPException(422, detail="Date of birth cannot be in the future")
    if body.date_of_birth < today - timedelta(days=365):
        raise HTTPException(422, detail="Date of birth must be within the last year")
    count = await session.scalar(
        select(func.count()).select_from(DemoBaby).where(DemoBaby.sandbox_id == sandbox.id)
    )
    if count >= settings.demo_max_babies_per_sandbox:
        raise HTTPException(
            429, detail=f"Limit reached: at most {settings.demo_max_babies_per_sandbox} babies per sandbox"
        )
    baby = DemoBaby(
        id=await _new_baby_id(session),
        sandbox_id=sandbox.id,
        date_of_birth=body.date_of_birth,
        ga_weeks=body.ga_weeks,
        ga_days=body.ga_days,
        created_at=utcnow(),
    )
    session.add(baby)
    await session.commit()
    return await _detail(session, sandbox, baby, settings)


@sandbox_router.delete(
    "/babies/{baby_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(limit_writes)]
)
async def delete_baby(
    baby_id: str,
    sandbox: DemoSandbox = Depends(current_sandbox),
    session: AsyncSession = Depends(get_session),
) -> Response:
    baby = await _get_baby(session, sandbox, baby_id)
    if baby.sandbox_id is None:
        raise _read_only()
    for scan in await _visible_scans(session, sandbox, baby.id):
        await session.delete(scan)
    await session.delete(baby)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@sandbox_router.post(
    "/babies/{baby_id}/scans",
    response_model=BabyDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_writes)],
)
async def add_scan(
    baby_id: str,
    body: ScanCreate,
    sandbox: DemoSandbox = Depends(current_sandbox),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BabyDetail:
    baby = await _get_baby(session, sandbox, baby_id)
    tz = ZoneInfo(settings.scan_day_timezone)
    measured_at = body.measured_at if body.measured_at.tzinfo else body.measured_at.replace(tzinfo=tz)
    if measured_at.astimezone(tz).date() < baby.date_of_birth:
        raise HTTPException(422, detail="Scan date is before the date of birth")
    if measured_at > utcnow() + timedelta(hours=1):
        raise HTTPException(422, detail="Scan date cannot be in the future")
    scans = await _visible_scans(session, sandbox, baby.id)
    if len(scans) >= settings.demo_max_scans_per_baby:
        raise HTTPException(
            429, detail=f"Limit reached: at most {settings.demo_max_scans_per_baby} scans per baby"
        )
    session.add(
        DemoScan(
            id=str(uuid.uuid4()),
            baby_id=baby.id,
            sandbox_id=sandbox.id,
            measured_at=measured_at.astimezone(ZoneInfo("UTC")),
            vi_left_mm=body.vi_left_mm,
            vi_right_mm=body.vi_right_mm,
            ahw_mm=body.ahw_mm,
            tod_mm=body.tod_mm,
            clinical_concern=body.clinical_concern.value,
            created_at=utcnow(),
        )
    )
    await session.commit()
    return await _detail(session, sandbox, baby, settings)


@sandbox_router.delete(
    "/babies/{baby_id}/scans/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(limit_writes)],
)
async def delete_scan(
    baby_id: str,
    scan_id: str,
    sandbox: DemoSandbox = Depends(current_sandbox),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await _get_baby(session, sandbox, baby_id)
    scan = await session.get(DemoScan, scan_id)
    if scan is None or scan.baby_id != baby_id or scan.sandbox_id not in (None, sandbox.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No scan {scan_id}")
    if scan.sandbox_id is None:
        raise _read_only()
    await session.delete(scan)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@sandbox_router.post(
    "/sandbox/reset", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(limit_writes)]
)
async def reset_sandbox(
    sandbox: DemoSandbox = Depends(current_sandbox),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Remove everything this visitor added; the 10 seed babies remain as they were."""
    await delete_sandbox_rows(session, [sandbox.id])
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

