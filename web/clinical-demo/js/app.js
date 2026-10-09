/**
 * Clinical demo: baby list → baby view (trend + explained bands) → add baby / add scan.
 * Hash routes: #/  ·  #/baby/DEMO-0003  ·  #/new
 */
import { CONFIG } from "./config.js";
import { api } from "./api.js";
import { renderMetricChart } from "./trend.js";

const app = document.getElementById("app");
const toastEl = document.getElementById("toast");
let renderSeq = 0;

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const dateFmt = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: CONFIG.timeZone });
const dateTimeFmt = new Intl.DateTimeFormat("en-GB", {
  day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: CONFIG.timeZone,
});
const fmtDate = (iso) => dateFmt.format(new Date(`${iso}T12:00:00Z`));
const fmtDateTime = (iso) => dateTimeFmt.format(new Date(iso));

function toast(msg, kind = "error") {
  toastEl.textContent = msg;
  toastEl.className = `toast toast--${kind}`;
  toastEl.hidden = false;
  clearTimeout(toast.t);
  toast.t = setTimeout(() => (toastEl.hidden = true), kind === "error" ? 7000 : 3000);
}

function bandChip(tier, score, { large = false } = {}) {
  if (!tier) return `<span class="band band--none">No band</span>`;
  const b = CONFIG.bands[tier];
  const scoreText = score == null ? "" : ` <span class="band__score">${score}/14</span>`;
  return `<span class="band band--${tier}${large ? " band--large" : ""}"><span class="band__dot" aria-hidden="true"></span>${b.label}${scoreText}</span>`;
}

function ruleSetChip(rs) {
  document.getElementById("ruleSet").textContent = `${rs.label} · ${rs.revision}`;
}

function provisionalNote(rs) {
  const unverified = rs.lines.filter((l) => l.kind === "reference_line" && l.verified === false);
  if (!unverified.length) return "";
  return `<p class="note">Reference-line values (${esc(unverified.map((l) => l.label).join(", "))}) are provisional until checked against the published chart by a clinician.</p>`;
}

// --- views ------------------------------------------------------------------------------------

async function viewList(seq) {
  const data = await api.listBabies();
  if (seq !== renderSeq) return;
  ruleSetChip(data.rule_set);
  const own = data.babies.filter((b) => !b.read_only);
  // All 10 seed babies stay in the database; the list shows a chosen few so it fits one screen.
  const listed = CONFIG.listedSeedBabies;
  const seed = data.babies.filter((b) => b.read_only && (!listed?.length || listed.includes(b.id)));
  const row = (b) => `
    <li>
      <a class="baby-row" href="#/baby/${encodeURIComponent(b.id)}">
        <span class="baby-row__id">${esc(b.id)}${b.read_only ? "" : ` <span class="tag">Yours</span>`}</span>
        <span class="baby-row__story">${esc(b.story ?? "Added in your sandbox")}</span>
        <span class="baby-row__meta">Born ${esc(b.ga_label)} wk · ${b.scan_count} scan${b.scan_count === 1 ? "" : "s"}${
          b.latest_age_label ? ` · latest at ${esc(b.latest_age_label)} wk` : ""
        }</span>
        <span class="baby-row__band">${
          b.latest_status === "not_scored" ? `<span class="band band--none">Not scored</span>` : bandChip(b.latest_risk_tier, b.latest_score)
        }</span>
      </a>
    </li>`;
  app.innerHTML = `
    <section class="intro">
      <h1>Demo NICU</h1>
      <p>Synthetic preterm babies scanned on a standard preterm timetable: admission, days 1–3 and 7, weekly to
      32 weeks, then 35 weeks, term and discharge. Open a baby to see its trend and how each band is worked out.
      Anything you add is visible only to you.</p>
      <div class="intro__actions">
        <a class="btn btn--primary" href="#/new">Add a baby</a>
        <span class="muted">${data.sandbox_baby_count} of ${data.max_babies} added</span>
      </div>
    </section>
    ${own.length ? `<h2 class="list-title">Your babies</h2><ul class="baby-list">${own.map(row).join("")}</ul>` : ""}
    <h2 class="list-title">Pre-loaded examples</h2>
    <ul class="baby-list">${seed.map(row).join("")}</ul>`;
}

function layerTable(a) {
  const r = a.result;
  const p = r.progression;
  const cell = (v) => (v == null ? "—" : v);
  return `
    <table class="layers">
      <thead><tr><th scope="col">Layer</th><th scope="col">VI</th><th scope="col">AHW</th><th scope="col">TOD</th><th scope="col">Points</th></tr></thead>
      <tbody>
        <tr><th scope="row">Size now</th><td>${r.static.vi_points}</td><td>${r.static.ahw_points}</td><td>${r.static.tod_points}</td><td>${r.static.static_score}</td></tr>
        <tr><th scope="row">Growth</th><td>${cell(p?.vi_points)}</td><td>${cell(p?.ahw_points)}</td><td>${cell(p?.tod_points)}</td><td>${p ? p.progression_score : "0"}</td></tr>
        <tr><th scope="row">Clinical</th><td colspan="3"></td><td>${r.clinical.clinical_modifier}</td></tr>
      </tbody>
      <tfoot><tr><th scope="row">Total</th><td colspan="3"></td><td>${r.numic_flow_score} / 14</td></tr></tfoot>
    </table>`;
}

function scanCard(scan, baby, index) {
  const a = scan.assessment;
  const calc = [
    scan.day_of_life != null ? `day ${scan.day_of_life}` : null,
    scan.age_label ? `${scan.age_label} wk` : null,
    a.result ? `VI line ${a.result.static.vi.reference_line_mm.toFixed(1)} mm` : null,
    a.result ? `${a.result.static.vi.distance_from_line_mm >= 0 ? "+" : ""}${a.result.static.vi.distance_from_line_mm.toFixed(1)} mm` : null,
  ].filter(Boolean);
  return `
    <article class="scan">
      <header class="scan__head">
        <div>
          <h3>Scan ${index + 1}${scan.protocol_label ? ` · ${esc(scan.protocol_label)}` : ""} · ${esc(fmtDateTime(scan.measured_at))}</h3>
          <p class="calc" title="Worked out from date of birth, gestational age and scan time">${esc(calc.join(" · "))}</p>
        </div>
        ${a.status === "scored" ? bandChip(a.risk_tier, a.numic_flow_score) : `<span class="band band--none">Not scored</span>`}
      </header>
      <dl class="measures">
        <div><dt>VI left / right</dt><dd>${scan.vi_left_mm} / ${scan.vi_right_mm} mm</dd></div>
        <div><dt>AHW</dt><dd>${scan.ahw_mm} mm</dd></div>
        <div><dt>TOD</dt><dd>${scan.tod_mm} mm</dd></div>
        <div><dt>Clinical concern</dt><dd>${esc(CONFIG.concern[scan.clinical_concern])}</dd></div>
      </dl>
      ${
        a.status === "scored"
          ? `<details class="why"${index === baby.scans.length - 1 ? " open" : ""}>
               <summary>Why this band</summary>
               ${layerTable(a)}
               <ul class="reasons">${a.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
             </details>`
          : `<p class="unscored">${esc(a.message)}</p>`
      }
      <footer class="scan__foot">
        <span class="muted">Rule ${esc(a.rule_revision)} · ${scan.read_only ? "pre-loaded scan" : "added by you"}</span>
        ${scan.read_only ? "" : `<button type="button" class="btn btn--link" data-delete-scan="${esc(scan.id)}">Delete scan</button>`}
      </footer>
    </article>`;
}

function localInputValue(d) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function addScanForm(baby) {
  if (!baby.can_add_scan) return `<p class="note">This baby has reached the demo limit of scans.</p>`;
  const num = (id, label) => `
    <div class="field"><label for="${id}">${label}</label>
      <input id="${id}" name="${id}" type="number" inputmode="decimal" step="0.1" min="0" max="${id === "tod_mm" ? 60 : 40}" required /></div>`;
  return `
    <form class="card add-scan" id="addScan" novalidate>
      <h2>Add a scan</h2>
      <p class="muted">Measurements in mm from the scan's calipers. VI is scored on the larger side.</p>
      <div class="field-grid">
        <div class="field field--wide"><label for="measured_at">Scan date and time</label>
          <input id="measured_at" name="measured_at" type="datetime-local" required
            min="${baby.date_of_birth}T00:00" max="${localInputValue(new Date())}" value="${localInputValue(new Date())}" /></div>
        ${num("vi_left_mm", "VI left")}
        ${num("vi_right_mm", "VI right")}
        ${num("ahw_mm", "AHW")}
        ${num("tod_mm", "TOD")}
      </div>
      <fieldset class="concern">
        <legend>Clinical concern</legend>
        ${Object.entries(CONFIG.concern)
          .map(
            ([v, label]) =>
              `<label class="radio"><input type="radio" name="clinical_concern" value="${v}"${v === "none" ? " checked" : ""} /> ${label}</label>`,
          )
          .join("")}
      </fieldset>
      <button type="submit" class="btn btn--primary">Score this scan</button>
    </form>`;
}

async function viewBaby(seq, id) {
  const baby = await api.getBaby(id);
  if (seq !== renderSeq) return;
  ruleSetChip(baby.rule_set);
  const latest = baby.scans[baby.scans.length - 1];
  const la = latest?.assessment;
  const summary = !latest
    ? `<p class="muted">No scans yet. Add the first scan below.</p>`
    : la.status === "scored"
      ? `${bandChip(la.risk_tier, la.numic_flow_score, { large: true })}
         <p class="summary__text">${esc(CONFIG.bands[la.risk_tier].text)} on the latest scan (${esc(latest.age_label)} wk).</p>`
      : `<span class="band band--none band--large">Not scored</span><p class="summary__text">${esc(la.message)}</p>`;
  const rules = Object.fromEntries(baby.rule_set.lines.map((l) => [l.metric, l]));

  app.innerHTML = `
    <a class="back" href="#/">← All babies</a>
    <section class="baby-head">
      <div>
        <h1>${esc(baby.id)}</h1>
        <p class="muted">Born ${esc(fmtDate(baby.date_of_birth))} at ${esc(baby.ga_label)} weeks · synthetic${
          baby.story ? ` · ${esc(baby.story)}` : ""
        }</p>
        <p class="muted">${baby.read_only ? "Pre-loaded example: shared and read-only. Scans you add stay in your sandbox." : "Added by you."}</p>
      </div>
      <div class="summary">${summary}</div>
    </section>

    <section class="card charts" aria-label="Measurement trends">
      <h2>Trend by age at scan</h2>
      <p class="muted chart-key">
        <span class="key-item"><span class="key key--line"></span>measurement</span>
        <span class="key-item"><span class="key key--ref1"></span>97th centile / ELVIS lower cut-off</span>
        <span class="key-item"><span class="key key--ref2"></span>97th centile + 4 mm / higher cut-off</span>
      </p>
      <div class="chart-grid">
        ${["vi", "ahw", "tod"]
          .map((m) => `<figure class="chart"><figcaption>${m.toUpperCase()} (mm)</figcaption><div class="chart__plot" data-metric="${m}"></div></figure>`)
          .join("")}
      </div>
      ${provisionalNote(baby.rule_set)}
    </section>

    <section aria-label="Scans">
      <h2 class="list-title">Scans and bands</h2>
      ${baby.scans.length ? baby.scans.map((s, i) => scanCard(s, baby, i)).reverse().join("") : ""}
    </section>

    ${addScanForm(baby)}

    ${baby.read_only ? "" : `<p><button type="button" class="btn btn--danger" id="deleteBaby">Delete this baby</button></p>`}`;

  const drawCharts = () =>
    app.querySelectorAll(".chart__plot").forEach((el) => renderMetricChart(el, el.dataset.metric, baby.scans, rules[el.dataset.metric]));
  drawCharts();
  observeResize(drawCharts);

  app.querySelectorAll("[data-delete-scan]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this scan from your sandbox?")) return;
      await guarded(() => api.deleteScan(baby.id, btn.dataset.deleteScan));
      route();
    }),
  );
  document.getElementById("deleteBaby")?.addEventListener("click", async () => {
    if (!confirm(`Delete ${baby.id} and its scans from your sandbox?`)) return;
    if (await guarded(() => api.deleteBaby(baby.id))) location.hash = "#/";
  });
  document.getElementById("addScan")?.addEventListener("submit", (e) => submitScan(e, baby));
}

async function submitScan(e, baby) {
  e.preventDefault();
  const form = e.target;
  if (!form.reportValidity()) return;
  const f = new FormData(form);
  const body = {
    measured_at: new Date(f.get("measured_at")).toISOString(),
    vi_left_mm: Number(f.get("vi_left_mm")),
    vi_right_mm: Number(f.get("vi_right_mm")),
    ahw_mm: Number(f.get("ahw_mm")),
    tod_mm: Number(f.get("tod_mm")),
    clinical_concern: f.get("clinical_concern"),
  };
  const btn = form.querySelector("button[type=submit]");
  btn.disabled = true;
  const ok = await guarded(() => api.addScan(baby.id, body));
  btn.disabled = false;
  if (ok) {
    toast("Scan added and scored.", "ok");
    await route();
    document.querySelector(".scan")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function viewNew() {
  const d = new Date();
  d.setDate(d.getDate() - CONFIG.newBabyDefaultAgeDays);
  const iso = (x) => x.toISOString().slice(0, 10);
  const minDob = new Date();
  minDob.setFullYear(minDob.getFullYear() - 1);
  app.innerHTML = `
    <a class="back" href="#/">← All babies</a>
    <form class="card add-baby" id="addBaby" novalidate>
      <h1>Add a baby</h1>
      <p class="muted">A patient ID such as DEMO-7K3Q is created for you. There are no name or ID fields:
      do not enter real patient details.</p>
      <div class="field-grid">
        <div class="field field--wide"><label for="dob">Date of birth (synthetic)</label>
          <input id="dob" name="dob" type="date" required value="${iso(d)}" min="${iso(minDob)}" max="${iso(new Date())}" /></div>
        <div class="field"><label for="gaw">GA at birth (weeks)</label>
          <select id="gaw" name="gaw">${Array.from({ length: 21 }, (_, i) => 22 + i)
            .map((w) => `<option${w === 28 ? " selected" : ""}>${w}</option>`)
            .join("")}</select></div>
        <div class="field"><label for="gad">+ days</label>
          <select id="gad" name="gad">${Array.from({ length: 7 }, (_, i) => `<option>${i}</option>`).join("")}</select></div>
      </div>
      <button type="submit" class="btn btn--primary">Add baby</button>
    </form>`;
  document.getElementById("addBaby").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!e.target.reportValidity()) return;
    const f = new FormData(e.target);
    const baby = await guarded(() =>
      api.addBaby({ date_of_birth: f.get("dob"), ga_weeks: Number(f.get("gaw")), ga_days: Number(f.get("gad")) }),
    );
    if (baby) location.hash = `#/baby/${encodeURIComponent(baby.id)}`;
  });
}

// --- plumbing ---------------------------------------------------------------------------------

let resizeObserver;
function observeResize(fn) {
  resizeObserver?.disconnect();
  if (typeof ResizeObserver === "undefined") return;
  let last = app.clientWidth;
  resizeObserver = new ResizeObserver(() => {
    if (app.clientWidth !== last) {
      last = app.clientWidth;
      fn();
    }
  });
  resizeObserver.observe(app);
}

async function guarded(fn) {
  try {
    return (await fn()) ?? true;
  } catch (err) {
    toast(err.message || "Something went wrong");
    return null;
  }
}

async function route() {
  const seq = ++renderSeq;
  resizeObserver?.disconnect();
  const hash = location.hash || "#/";
  try {
    const baby = hash.match(/^#\/baby\/(.+)$/);
    if (baby) await viewBaby(seq, decodeURIComponent(baby[1]));
    else if (hash === "#/new") viewNew();
    else await viewList(seq);
  } catch (err) {
    if (seq !== renderSeq) return;
    app.innerHTML = `<a class="back" href="#/">← All babies</a><p class="error">${esc(err.message || "Could not load the demo.")}</p>`;
  }
  if (seq === renderSeq) window.scrollTo({ top: 0 });
}

document.getElementById("resetBtn").addEventListener("click", async () => {
  if (!confirm("Remove everything you added? The 10 pre-loaded babies stay as they are.")) return;
  if (await guarded(() => api.resetSandbox())) {
    toast("Your sandbox has been reset.", "ok");
    location.hash = "#/";
    route();
  }
});

window.addEventListener("hashchange", route);
route();
