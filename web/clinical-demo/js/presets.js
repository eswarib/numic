/**
 * Synthetic prior + current pairs validated against numic_flow_v1 static/progression rules.
 * Add real anonymised vignettes here or load from a future `/examples` API.
 */
export const PRESETS = {
  low: {
    viP97Ref: 12,
    prior: { vi: 8, ahw: 4, tod: 22, pct: 85 },
    current: { vi: 8, ahw: 4, tod: 22, pct: 85 },
  },
  moderate: {
    viP97Ref: 12,
    prior: { vi: 8, ahw: 5, tod: 22, pct: 95 },
    current: { vi: 9, ahw: 6, tod: 24, pct: 98 },
  },
  high: {
    viP97Ref: 12,
    prior: { vi: 14, ahw: 9, tod: 28, pct: 98 },
    current: { vi: 18, ahw: 11, tod: 35, pct: 99 },
  },
};

export function defaultDatetimePair() {
  const current = new Date();
  current.setHours(9, 0, 0, 0);
  const prior = new Date(current);
  prior.setDate(prior.getDate() - 2);
  const isoLocal = (d) => {
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };
  return { prior: isoLocal(prior), current: isoLocal(current) };
}

/**
 * @param {"low"|"moderate"|"high"} key
 */
export function applyPreset(key) {
  const p = PRESETS[key];
  if (!p) return;

  document.getElementById("viP97Ref").value = String(p.viP97Ref);
  const { prior: dtPrior, current: dtCur } = defaultDatetimePair();
  document.getElementById("dt-prior").value = dtPrior;
  document.getElementById("dt-current").value = dtCur;

  document.getElementById("vi-prior").value = p.prior.vi;
  document.getElementById("ahw-prior").value = p.prior.ahw;
  document.getElementById("tod-prior").value = p.prior.tod;
  document.getElementById("pct-prior").value = p.prior.pct;

  document.getElementById("vi-current").value = p.current.vi;
  document.getElementById("ahw-current").value = p.current.ahw;
  document.getElementById("tod-current").value = p.current.tod;
  document.getElementById("pct-current").value = p.current.pct;
}
