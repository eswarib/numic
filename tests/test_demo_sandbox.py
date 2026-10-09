"""Public demo: seed babies, private sandboxes, limits and clean-up (DEMO requirements)."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from numic.core.config import get_settings
from numic.demo.models import DemoBaby, DemoSandbox, DemoScan
from numic.demo.router import SANDBOX_HEADER, write_limiter
from numic.demo.seed import apply_seed, delete_expired_sandboxes, load_seed
from numic.demo.service import score_scans
from numic.main import app
from numic.scoring.rules import get_rules


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("NUMIC_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/demo.db")
    get_settings.cache_clear()
    write_limiter._hits.clear()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


class Visitor:
    """One browser: keeps the sandbox token the server hands out, like the demo UI does."""

    def __init__(self, client: TestClient) -> None:
        self.client = client
        self.token: str | None = None

    def request(self, method: str, url: str, **kw):
        headers = {SANDBOX_HEADER: self.token} if self.token else {}
        r = self.client.request(method, f"/api/v1/demo{url}", headers=headers, **kw)
        self.token = r.headers.get(SANDBOX_HEADER, self.token)
        return r

    def babies(self) -> dict[str, dict]:
        r = self.request("GET", "/babies")
        assert r.status_code == 200
        return {b["id"]: b for b in r.json()["babies"]}

    def baby(self, baby_id: str) -> dict:
        r = self.request("GET", f"/babies/{baby_id}")
        assert r.status_code == 200
        return r.json()


def _scan(when: datetime, vi: float = 12.0, **kw) -> dict:
    return {
        "measured_at": when.isoformat(),
        "vi_left_mm": vi,
        "vi_right_mm": vi - 0.3,
        "ahw_mm": kw.get("ahw", 6.5),
        "tod_mm": kw.get("tod", 25.0),
        "clinical_concern": kw.get("concern", "none"),
    }


def _db(client: TestClient, fn):
    async def run():
        async with app.state.demo_db.sessionmaker() as session:
            return await fn(session)

    return client.portal.call(run)


# --- seed set -----------------------------------------------------------------------------------


def test_new_visitor_sees_ten_seed_babies(client) -> None:
    babies = Visitor(client).babies()
    assert len(babies) == 10
    assert all(b["read_only"] for b in babies.values())
    counts = sorted(b["scan_count"] for b in babies.values())
    assert counts[0] == 1 and all(c >= 2 for c in counts[1:])  # one baby with only a first scan


def test_seed_band_mix_and_special_cases(client) -> None:
    v = Visitor(client)
    babies = v.babies()
    bands = Counter(b["latest_risk_tier"] for b in babies.values())
    assert bands["high"] >= 2
    assert bands["moderate"] >= 1
    assert bands["low"] > bands["moderate"] + bands["high"] - 1  # mostly low
    assert babies["DEMO-0004"]["scan_count"] == 1

    not_scored = [
        (b_id, s)
        for b_id in babies
        for s in v.baby(b_id)["scans"]
        if s["assessment"]["status"] == "not_scored"
    ]
    assert not_scored and {b_id for b_id, _ in not_scored} == {"DEMO-0009"}
    assert all("outside" in scan["assessment"]["message"] for _, scan in not_scored)
    assert all(scan["age_weeks"] < 26 for _, scan in not_scored)


@pytest.mark.parametrize("today", [date(2026, 3, 29), date(2026, 10, 25), date(2027, 2, 28)])
def test_seed_ages_are_realistic_on_any_date(client, today) -> None:
    """DEMO-F05: re-dated seed scans fall at the same plausible ages whatever today is."""
    tz = "Europe/London"
    rules = get_rules()

    async def check(session):
        await apply_seed(session, today, tz)
        ages = {}
        for sb in load_seed():
            baby = await session.get(DemoBaby, sb.id)
            scans = list(await session.scalars(select(DemoScan).where(DemoScan.baby_id == sb.id)))
            scored = score_scans(baby, scans, rules, tz)
            assert [s.day_of_life for s in scored] == [s.day for s in sb.scans]
            assert all(s.measured_at.date() <= today for s in scored)
            ages[sb.id] = [s.age_label for s in scored]
        return ages

    ages = _db(client, check)
    assert ages["DEMO-0001"][:5] == ["26+0", "26+1", "26+2", "26+3", "27+0"]
    assert ages["DEMO-0001"][-3:] == ["35+0", "40+0", "40+5"]  # 35 weeks, term corrected, discharge
    assert ages["DEMO-0009"][0] == "25+4"  # the intentional out-of-chart case


def test_seed_scans_follow_the_protocol(client) -> None:
    detail = Visitor(client).baby("DEMO-0001")
    labels = [s["protocol_label"] for s in detail["scans"]]
    assert labels == ["Admission", "Day 1", "Day 2", "Day 3", "Day 7"] + ["Weekly"] * 5 + [
        "35 weeks",
        "Term corrected",
        "Discharge",
    ]


def test_seed_result_is_explained(client) -> None:
    detail = Visitor(client).baby("DEMO-0006")
    latest = detail["scans"][-1]["assessment"]
    assert latest["rule_revision"] == "numic_flow_levene@1"
    assert latest["risk_tier"] == "moderate"
    assert any("Levene" in r for r in latest["reasons"])
    assert latest["result"]["static"]["vi"]["reference_line_mm"] is not None
    vi_line = next(line for line in detail["rule_set"]["lines"] if line["metric"] == "vi")
    assert vi_line["kind"] == "reference_line" and vi_line["two_point_offset_mm"] == 4


def test_band_wording_has_no_treatment_instructions(client) -> None:
    """DEMO-F13: reasons describe measurements and points only."""
    v = Visitor(client)
    banned = re.compile(r"\b(refer|escalat|treat|tap|lumbar|shunt|reservoir|should|must)\w*", re.I)
    for b_id in v.babies():
        for scan in v.baby(b_id)["scans"]:
            for reason in scan["assessment"]["reasons"]:
                assert not banned.search(reason), reason


# --- sandboxes ----------------------------------------------------------------------------------


def test_scan_on_seed_baby_is_private_to_the_sandbox(client) -> None:
    a, b = Visitor(client), Visitor(client)
    a.babies(), b.babies()
    assert a.token and b.token and a.token != b.token

    seed_before = len(b.baby("DEMO-0003")["scans"])
    when = datetime.now(timezone.utc) - timedelta(hours=2)
    r = a.request("POST", "/babies/DEMO-0003/scans", json=_scan(when, vi=13.0))
    assert r.status_code == 201
    assert len(r.json()["scans"]) == seed_before + 1
    assert r.json()["scans"][-1]["read_only"] is False

    assert len(a.baby("DEMO-0003")["scans"]) == seed_before + 1
    assert len(b.baby("DEMO-0003")["scans"]) == seed_before

    async def seed_rows(session):
        rows = await session.scalars(
            select(DemoScan).where(DemoScan.baby_id == "DEMO-0003", DemoScan.sandbox_id.is_(None))
        )
        return len(list(rows))

    assert _db(client, seed_rows) == seed_before


def test_missing_or_unknown_token_gets_a_new_sandbox(client) -> None:
    a = Visitor(client)
    a.request("POST", "/babies", json={"date_of_birth": str(date.today() - timedelta(days=3)), "ga_weeks": 28})
    stranger = Visitor(client)
    stranger.token = "x" * 30  # well-formed but unknown
    stranger.babies()
    assert stranger.token not in (a.token, "x" * 30)
    assert len(stranger.babies()) == 10


def test_add_baby_generates_id_and_rejects_identifying_fields(client) -> None:
    v = Visitor(client)
    dob = str(date.today() - timedelta(days=5))
    r = v.request("POST", "/babies", json={"date_of_birth": dob, "ga_weeks": 27, "ga_days": 3})
    assert r.status_code == 201
    data = r.json()
    assert re.fullmatch(r"DEMO-[2-9A-HJ-NP-Z]{4}", data["id"])
    assert data["read_only"] is False and data["ga_label"] == "27+3"
    assert next(iter(v.babies())) == data["id"]  # own babies listed first

    for extra in ({"id": "MRN123"}, {"name": "Baby Smith"}, {"notes": "free text"}):
        r = v.request("POST", "/babies", json={"date_of_birth": dob, "ga_weeks": 27, **extra})
        assert r.status_code == 422


def test_scan_rejects_free_text_and_dates_before_birth(client) -> None:
    v = Visitor(client)
    dob = date.today() - timedelta(days=5)
    baby = v.request("POST", "/babies", json={"date_of_birth": str(dob), "ga_weeks": 28}).json()
    when = datetime.now(timezone.utc) - timedelta(hours=1)
    r = v.request("POST", f"/babies/{baby['id']}/scans", json={**_scan(when), "notes": "hello"})
    assert r.status_code == 422
    before = datetime.combine(dob - timedelta(days=1), datetime.min.time(), timezone.utc)
    r = v.request("POST", f"/babies/{baby['id']}/scans", json=_scan(before))
    assert r.status_code == 422


def test_seed_rows_cannot_be_changed(client) -> None:
    v = Visitor(client)
    assert v.request("DELETE", "/babies/DEMO-0001").status_code == 403
    assert v.request("DELETE", "/babies/DEMO-0001/scans/DEMO-0001-S1").status_code == 403


def test_other_sandbox_rows_are_invisible(client) -> None:
    a, b = Visitor(client), Visitor(client)
    dob = str(date.today() - timedelta(days=4))
    baby = a.request("POST", "/babies", json={"date_of_birth": dob, "ga_weeks": 30}).json()
    b.babies()
    assert baby["id"] not in b.babies()
    assert b.request("GET", f"/babies/{baby['id']}").status_code == 404
    assert b.request("DELETE", f"/babies/{baby['id']}").status_code == 404


def test_reset_removes_only_my_additions(client) -> None:
    v = Visitor(client)
    original = {k: b["scan_count"] for k, b in v.babies().items()}
    when = datetime.now(timezone.utc) - timedelta(hours=1)
    v.request("POST", "/babies/DEMO-0005/scans", json=_scan(when))
    v.request("POST", "/babies", json={"date_of_birth": str(date.today()), "ga_weeks": 26})
    assert len(v.babies()) == 11

    assert v.request("POST", "/sandbox/reset").status_code == 204
    assert {k: b["scan_count"] for k, b in v.babies().items()} == original


def test_inactive_sandboxes_are_deleted(client) -> None:
    v = Visitor(client)
    baby = v.request("POST", "/babies", json={"date_of_birth": str(date.today()), "ga_weeks": 29}).json()
    when = datetime.now(timezone.utc) - timedelta(minutes=30)
    v.request("POST", f"/babies/{baby['id']}/scans", json=_scan(when))
    v.request("POST", "/babies/DEMO-0002/scans", json=_scan(when))

    async def age_and_clean(session):
        sb = await session.get(DemoSandbox, v.token)
        sb.last_seen_at = datetime.now(timezone.utc) - timedelta(days=8)
        await session.commit()
        removed = await delete_expired_sandboxes(session, ttl_days=7)
        left = await session.scalars(select(DemoScan).where(DemoScan.sandbox_id == v.token))
        return removed, await session.get(DemoSandbox, v.token), await session.get(DemoBaby, baby["id"]), list(left)

    removed, sandbox, gone_baby, scans = _db(client, age_and_clean)
    assert removed == 1 and sandbox is None and gone_baby is None and scans == []


def test_redating_moves_visitor_scans_on_seed_babies(client) -> None:
    v = Visitor(client)
    when = datetime.now(timezone.utc) - timedelta(hours=1)
    v.request("POST", "/babies/DEMO-0001/scans", json=_scan(when))
    before = v.baby("DEMO-0001")["scans"][-1]["day_of_life"]

    async def redate(session):
        baby = await session.get(DemoBaby, "DEMO-0001")
        await apply_seed(session, baby.date_of_birth + timedelta(days=baby.seed_born_days_ago + 1), "Europe/London")

    _db(client, redate)
    assert v.baby("DEMO-0001")["scans"][-1]["day_of_life"] == before


# --- limits -------------------------------------------------------------------------------------


def test_baby_limit_returns_429(client, monkeypatch) -> None:
    monkeypatch.setenv("NUMIC_DEMO_MAX_BABIES_PER_SANDBOX", "2")
    get_settings.cache_clear()
    v = Visitor(client)
    body = {"date_of_birth": str(date.today()), "ga_weeks": 30}
    assert [v.request("POST", "/babies", json=body).status_code for _ in range(3)] == [201, 201, 429]
    assert "2 babies" in v.request("POST", "/babies", json=body).json()["detail"]


def test_write_rate_limit_returns_429(client, monkeypatch) -> None:
    monkeypatch.setenv("NUMIC_DEMO_WRITES_PER_MINUTE", "3")
    get_settings.cache_clear()
    v = Visitor(client)
    codes = [v.request("POST", "/sandbox/reset").status_code for _ in range(4)]
    assert codes == [204, 204, 204, 429]
    assert v.request("GET", "/babies").status_code == 200  # reads are not limited
