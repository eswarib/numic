# NUMIC clinical demo (web UI)

Browser UI for **demonstrating** NumicFlow scoring with a neonatologist-appropriate story: **prior vs current mm** (overlay/calipers path), **clinical modifier 0/1/2**, and **versioned rule bundles**.

## Run it

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn numic.main:app --reload --host 127.0.0.1 --port 8000
```

Then open [http://127.0.0.1:8000/clinical-demo/](http://127.0.0.1:8000/clinical-demo/). The UI talks to the API on the **same origin** (no CORS in this demo).

Other useful URLs: `/health`, `/docs` (OpenAPI).

## Code layout (`web/clinical-demo/`)

Static HTML/CSS and **ES modules** under `web/clinical-demo/js/`. FastAPI mounts this tree at **`/clinical-demo/`** when the directory exists (`src/numic/main.py`).

- **`js/config.js`** — API base paths, measurement `entry_source`, feature flags (e.g. future image pipeline). Prefer toggles here instead of scattered literals.
- **`js/api.js`** — `fetch` helpers; add auth and env-specific base URLs here for a production shell.
- **`js/presets.js`** — Synthetic prior/current pairs; extend with anonymised teaching cases or a future examples API.
- **`js/measurements.js`** — Form → `PatientMeasurementRecord`; natural place to attach PACS metadata later.
- **`js/app.js`** — Event wiring and hub/risk panel updates; keep thin so a SPA can reuse the modules.

## Product note

This is **decision-support demonstration** content only, not a regulated IFU. Copy and behaviour are aligned with the stakeholder charter (overlay-first, pairwise progression, clinical 0/1/2 for now).
