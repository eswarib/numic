/**
 * Clinical demo bootstrap — thin orchestration; extend with routing, state store, or a framework shell.
 */
import { CONFIG } from "./config.js";
import { postDemoNumicFlow, fetchScoreVersions } from "./api.js";
import { applyPreset, PRESETS } from "./presets.js";
import { readScan, buildRecord, clinicalPayload } from "./measurements.js";

function setTierUi(tier) {
  document.querySelectorAll(".risk-item").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".decision-card").forEach((el) => el.classList.remove("active"));
  const map = {
    low: { risk: "riskLow", dec: "decLow" },
    moderate: { risk: "riskMod", dec: "decMod" },
    high: { risk: "riskHigh", dec: "decHigh" },
  };
  const m = tier ? map[tier] : null;
  if (m) {
    document.getElementById(m.risk).classList.add("active");
    document.getElementById(m.dec).classList.add("active");
  }
}

function showError(msg) {
  const box = document.getElementById("errorBox");
  box.textContent = msg;
  box.hidden = false;
}

function clearError() {
  const box = document.getElementById("errorBox");
  box.hidden = true;
  box.textContent = "";
}

async function loadScoreVersions() {
  const sel = document.getElementById("scoreVersion");
  try {
    const data = await fetchScoreVersions();
    const versions = data.score_versions || [];
    sel.innerHTML = versions.map((v) => `<option value="${v}">${v}</option>`).join("");
    if (!versions.length) sel.innerHTML = '<option value="numic_flow_v1">numic_flow_v1</option>';
  } catch {
    sel.innerHTML = '<option value="numic_flow_v1">numic_flow_v1</option>';
  }
}

async function runScore() {
  clearError();
  const scoreVersion = document.getElementById("scoreVersion").value;
  const current = readScan("current");
  if (!current) {
    showError("Enter VI, AHW, TOD, and VI percentile for the current scan (mm from overlay / calipers).");
    return;
  }

  const includePrior = document.getElementById("includeProgression")?.checked ?? true;
  const priorRaw = includePrior ? readScan("prior") : null;

  const record = buildRecord(current, { isCurrent: true });
  let prior_record = null;
  if (priorRaw) {
    prior_record = buildRecord(priorRaw, { isCurrent: false });
  }

  const body = {
    score_version: scoreVersion,
    record,
    prior_record,
    clinical: clinicalPayload(),
  };

  const btn = document.getElementById("calcBtn");
  btn.disabled = true;
  try {
    const r = await postDemoNumicFlow(body);
    const text = await r.text();
    if (!r.ok) {
      let detail = text;
      try {
        const j = JSON.parse(text);
        detail = j.detail ?? text;
        if (typeof detail === "object") detail = JSON.stringify(detail);
      } catch {
        /* noop */
      }
      showError(String(detail || `HTTP ${r.status}`));
      document.getElementById("totalScore").textContent = "—";
      document.getElementById("scoreVersionOut").textContent = "";
      setTierUi(null);
      return;
    }
    const data = JSON.parse(text);
    document.getElementById("totalScore").textContent = String(data.numic_flow_score);
    document.getElementById("scoreVersionOut").textContent = `Bundle: ${data.score_version}`;
    setTierUi(data.risk_tier);
    document.getElementById("breakdownPre").textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    showError(e.message || "Request failed");
  } finally {
    btn.disabled = false;
  }
}

function togglePriorPanelDisabled(disabled) {
  document.querySelectorAll("[data-scan-group='prior']").forEach((el) => {
    el.disabled = disabled;
  });
}

function wireProgressionToggle() {
  const cb = document.getElementById("includeProgression");
  if (!cb) return;
  const sync = () => togglePriorPanelDisabled(!cb.checked);
  cb.addEventListener("change", sync);
  sync();
}

async function init() {
  applyPreset("low");
  document.getElementById("scenarioPreset").value = "low";
  await loadScoreVersions();
  wireProgressionToggle();

  document.getElementById("scenarioPreset").addEventListener("change", (e) => {
    const v = e.target.value;
    if (v && PRESETS[v]) applyPreset(v);
  });

  document.getElementById("calcBtn").addEventListener("click", runScore);

  await runScore();
}

init().catch(console.error);

// Expose for future embedding tests or e2e hooks
globalThis.__NUMIC_DEMO__ = { CONFIG, runScore, applyPreset };
