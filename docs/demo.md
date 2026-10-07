# NUMIC clinical demo (web UI)

Public demo of NumicFlow scoring for investors, accelerators and clinicians. It implements the **DEMO** requirements
(`docs/design/requirements/DEMO_public_demo.html`, v2): the real Python backend, the `numic_flow_levene` rule set,
10 pre-loaded synthetic babies, and a private sandbox per visitor. **Synthetic data only.**

Full details, including every setting, the PostgreSQL tables and the Railway configuration:
[`docs/design/NUMIC_clinical_demo.html`](design/NUMIC_clinical_demo.html).

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn numic.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/> (redirects to `/clinical-demo/`). With no database configured the demo uses a local
SQLite file, `numic-demo.db`; set `NUMIC_DATABASE_URL` (or `DATABASE_URL`) to use PostgreSQL. Tables are created
and the seed babies loaded on start-up. Tests: `pytest`.

Other useful URLs: `/health`, `/docs` (OpenAPI).

## What a visitor can do

- **Baby list**: 10 shared, read-only seed babies (`DEMO-0001`…`DEMO-0010`) plus any they added.
- **Baby view**: trend charts of VI, AHW and TOD over **age at scan**, with the Levene 97th-centile line and the
  line + 4 mm for VI and the fixed AHW/TOD cut-offs; every scan's band with layer points, plain-language reasons
  and the rule revision (`numic_flow_levene@1`). Day of life and age at scan are worked out, never typed.
- **Add a baby**: date of birth (synthetic, defaults to a week ago) and gestational age at birth (weeks + days).
  The patient ID (e.g. `DEMO-7K3Q`) is generated; there are no name, ID or free-text fields.
- **Add a scan** to any baby, including seed babies: date/time, VI left and right (the larger is scored), AHW, TOD,
  clinical concern. Scans added to a seed baby are visible only in that visitor's sandbox.
- **Reset my sandbox** removes everything the visitor added.

## How it works

| Piece | Where |
|---|---|
| Rule set (thresholds, bands, revision) | `src/numic/rule_sets/numic_flow_levene.json` |
| Levene VI 97th-centile table | `src/numic/rule_sets/tables/levene_vi_p97.json` — **provisional values, `verified: false`** |
| Age at scan, line lookup, out-of-range refusal | `src/numic/scoring/nomogram/` |
| Scoring + plain-language reasons | `src/numic/scoring/numic_flow.py` |
| Demo API (`/api/v1/demo/...`) | `src/numic/demo/router.py` |
| Seed babies (dates as offsets from today) | `src/numic/demo/seed_babies.json`, `src/numic/demo/seed.py` |
| Demo tables | `src/numic/demo/models.py` (portable: PostgreSQL or SQLite) |
| UI | `web/clinical-demo/` — `js/app.js` (views), `js/api.js` (sandbox header), `js/trend.js` (charts), `js/config.js` (display text) |

**Sandboxes.** The browser keeps a random token in `localStorage` and sends it in the `X-Demo-Sandbox` header (a
header, not a cookie, so the demo works inside an embedded frame). A request without a valid token gets a new
sandbox. Every query returns seed rows plus the current sandbox's rows. Seed rows return 403 on delete.

**Seed dates.** Seed babies are stored as "born N days ago, scanned on day k at HH:MM" and re-dated on start-up and
when the day changes, so ages stay realistic. Visitor scans on seed babies move with them.

**Seed spread.** 6 low, 2 moderate, 2 high; `DEMO-0004` has only a first scan; `DEMO-0009`'s first scan (24+5 wk)
is outside the Levene chart and shows "Not scored" rather than a guessed line. `tests/test_demo_sandbox.py` checks this.

**Limits and clean-up** (Tier 2 settings, `NUMIC_` env prefix): 20 babies per sandbox
(`NUMIC_DEMO_MAX_BABIES_PER_SANDBOX`), 30 scans per baby (`NUMIC_DEMO_MAX_SCANS_PER_BABY`), 60 writes per minute
per IP (`NUMIC_DEMO_WRITES_PER_MINUTE`) — over a limit returns 429 naming the limit. Sandboxes unused for 7 days
(`NUMIC_DEMO_SANDBOX_TTL_DAYS`) are deleted with their data by an hourly job.

**Privacy.** No cookies or tracking. The token is random and not linked to the visitor. The app logs only uvicorn's
access line (method, path, status); request bodies and the sandbox header are never logged.

## Deploying to demo.numic.uk (Railway)

1. Create a **separate** Railway project for the demo (DEMO-N02) with a PostgreSQL database and a service from this
   repository. `railway.json` sets the start command, `/health` check, one replica and no sleeping (DEMO-N05).
2. In the service variables, reference the database: `DATABASE_URL=${{Postgres.DATABASE_URL}}` (the `postgres://`
   form is converted to `postgresql+asyncpg://` automatically).
   Also set `NIXPACKS_PYTHON_VERSION=3.12` to pin Python (the project needs 3.11+). Keep one replica and one
   uvicorn worker: the write limiter and the hourly clean-up job run in-process.
3. Add the custom domain `demo.numic.uk` in Railway; at Namecheap add the **CNAME** record `demo` → the target
   Railway shows. Railway issues the certificate.
4. On the Carrd site (numic.uk), point the demo button at `https://demo.numic.uk/`.

## Before launch (open items from the requirements)

- **Blocker:** replace the provisional Levene 97th-centile values with values read from Levene 1981 and have a
  clinician check them; then set `"verified": true` (the UI note disappears).
- Clinician review of the seed babies' scan histories for realism.
- Confirm sandbox retention (7 days) and limits (20 babies, 30 scans, 60 writes/min).

## Product note

This is **decision-support demonstration** content only, not a regulated IFU. Band wording is neutral and gives no
treatment instructions.
