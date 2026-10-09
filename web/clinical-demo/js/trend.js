/**
 * Trend charts over age at scan (weeks). One chart per measurement, each a single series with
 * the rule set's thresholds: the Levene line and line + 4 mm for VI, fixed cut-offs for AHW / TOD.
 * Pure SVG; no chart library.
 */

const METRICS = {
  vi: { label: "VI", key: "vi_mm", title: "Ventricular index (larger side)" },
  ahw: { label: "AHW", key: "ahw_mm", title: "Anterior horn width" },
  tod: { label: "TOD", key: "tod_mm", title: "Thalamo-occipital distance" },
};

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function ga(weeks) {
  const days = Math.round(weeks * 7);
  return `${Math.floor(days / 7)}+${days % 7}`;
}

/** Linear interpolation in the table; null outside it (never extrapolated). */
function lineAt(points, age) {
  if (!points.length || age < points[0][0] || age > points[points.length - 1][0]) return null;
  for (let i = 1; i < points.length; i++) {
    const [a0, v0] = points[i - 1];
    const [a1, v1] = points[i];
    if (age <= a1) return v0 + ((v1 - v0) * (age - a0)) / (a1 - a0);
  }
  return points[points.length - 1][1];
}

/** Thresholds to draw for one metric as polylines of [age, mm]. */
function thresholdLines(rule, x0, x1) {
  if (!rule) return [];
  if (rule.kind === "fixed") {
    return [
      { label: `${rule.one_point_mm} mm`, cls: "ref-1", pts: [[x0, rule.one_point_mm], [x1, rule.one_point_mm]] },
      { label: `${rule.two_point_mm} mm`, cls: "ref-2", pts: [[x0, rule.two_point_mm], [x1, rule.two_point_mm]] },
    ];
  }
  const table = rule.points;
  const lo = Math.max(x0, table[0][0]);
  const hi = Math.min(x1, table[table.length - 1][0]);
  if (lo >= hi) return [];
  const ages = [lo, ...table.map((p) => p[0]).filter((a) => a > lo && a < hi), hi];
  const offset = (d) => ages.map((a) => [a, lineAt(table, a) + d]);
  return [
    { label: "97th centile", cls: "ref-1", pts: offset(rule.one_point_offset_mm) },
    { label: `+${rule.two_point_offset_mm} mm`, cls: "ref-2", pts: offset(rule.two_point_offset_mm) },
  ];
}

/**
 * @param {HTMLElement} host
 * @param {"vi"|"ahw"|"tod"} metric
 * @param {Array<object>} scans ScanOut from the API (any order)
 * @param {object|undefined} rule ReferenceLine for this metric from the rule set
 */
export function renderMetricChart(host, metric, scans, rule) {
  const m = METRICS[metric];
  const pts = scans
    .filter((s) => typeof s.age_weeks === "number")
    .map((s) => ({ x: s.age_weeks, y: s[m.key], scan: s }))
    .sort((a, b) => a.x - b.x);

  host.innerHTML = "";
  if (!pts.length) {
    host.innerHTML = `<p class="chart-empty">No scans to plot yet.</p>`;
    return;
  }

  const w = Math.max(260, host.clientWidth || 320);
  const h = 170;
  const pad = { top: 14, right: 64, bottom: 30, left: 36 };
  const pw = w - pad.left - pad.right;
  const ph = h - pad.top - pad.bottom;

  let x0 = Math.min(...pts.map((p) => p.x));
  let x1 = Math.max(...pts.map((p) => p.x));
  const span = Math.max(1.5, x1 - x0);
  x0 -= span * 0.12;
  x1 += span * 0.12;

  const lines = thresholdLines(rule, x0, x1);
  const ys = [...pts.map((p) => p.y), ...lines.flatMap((l) => l.pts.map((p) => p[1]))];
  let y0 = Math.min(...ys);
  let y1 = Math.max(...ys);
  const yPad = Math.max(1, (y1 - y0) * 0.12);
  y0 = Math.max(0, Math.floor(y0 - yPad));
  y1 = Math.ceil(y1 + yPad);

  const X = (v) => pad.left + ((v - x0) / (x1 - x0)) * pw;
  const Y = (v) => pad.top + ph - ((v - y0) / (y1 - y0)) * ph;
  const path = (arr) => arr.map(([a, b], i) => `${i ? "L" : "M"}${X(a).toFixed(1)},${Y(b).toFixed(1)}`).join(" ");

  const yTicks = [];
  const step = Math.max(1, Math.ceil((y1 - y0) / 4));
  for (let v = y0; v <= y1; v += step) yTicks.push(v);
  const xTicks = [];
  for (let v = Math.ceil(x0); v <= Math.floor(x1); v += x1 - x0 > 8 ? 2 : 1) xTicks.push(v);

  const grid =
    yTicks
      .map(
        (v) =>
          `<line class="grid" x1="${pad.left}" x2="${pad.left + pw}" y1="${Y(v)}" y2="${Y(v)}"/>` +
          `<text class="tick" x="${pad.left - 6}" y="${Y(v) + 3}" text-anchor="end">${v}</text>`,
      )
      .join("") +
    xTicks
      .map((v) => `<text class="tick" x="${X(v)}" y="${h - 14}" text-anchor="middle">${v}</text>`)
      .join("") +
    `<text class="axis-label" x="${pad.left + pw / 2}" y="${h - 1}" text-anchor="middle">Age at scan (weeks)</text>` +
    `<line class="axis" x1="${pad.left}" x2="${pad.left + pw}" y1="${pad.top + ph}" y2="${pad.top + ph}"/>`;

  const refs = lines
    .map((l) => {
      const [ax, ay] = l.pts[l.pts.length - 1];
      return (
        `<path class="ref ${l.cls}" d="${path(l.pts)}"/>` +
        `<text class="ref-label" x="${X(ax) + 4}" y="${Y(ay) + 3}">${esc(l.label)}</text>`
      );
    })
    .join("");

  const series =
    `<path class="series" d="${path(pts.map((p) => [p.x, p.y]))}"/>` +
    pts
      .map(
        (p, i) =>
          `<circle class="point${p.scan.assessment.status === "scored" ? "" : " point--unscored"}" cx="${X(p.x)}" cy="${Y(p.y)}" r="4.5"/>` +
          `<circle class="hit" data-i="${i}" cx="${X(p.x)}" cy="${Y(p.y)}" r="14" tabindex="0"` +
          ` aria-label="${esc(`${m.label} ${p.y} mm at ${ga(p.x)} weeks`)}"/>`,
      )
      .join("");

  host.innerHTML =
    `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" role="img" aria-label="${esc(`${m.title} by age at scan`)}">` +
    grid +
    refs +
    series +
    `</svg><div class="tooltip" hidden></div>`;

  const tip = host.querySelector(".tooltip");
  const show = (el) => {
    const p = pts[Number(el.dataset.i)];
    const a = p.scan.assessment;
    let extra = "";
    if (metric === "vi" && a.result) {
      const vi = a.result.static.vi;
      const d = vi.distance_from_line_mm;
      extra = `<div>Line ${vi.reference_line_mm.toFixed(1)} mm · ${d >= 0 ? "+" : ""}${d.toFixed(1)} mm</div>`;
    } else if (metric === "vi" && a.status !== "scored") {
      extra = `<div>Outside chart range</div>`;
    }
    tip.innerHTML =
      `<strong>${m.label} ${p.y} mm</strong><div>${p.scan.protocol_label ? `${esc(p.scan.protocol_label)} · ` : ""}${ga(p.x)} wk · day ${p.scan.day_of_life}</div>${extra}`;
    tip.hidden = false;
    const left = Math.min(Math.max(X(p.x) - 60, 0), w - 130);
    tip.style.left = `${(left / w) * 100}%`;
    tip.style.top = `${Math.max(0, Y(p.y) - 70)}px`;
  };
  host.querySelectorAll(".hit").forEach((el) => {
    el.addEventListener("pointerenter", () => show(el));
    el.addEventListener("focus", () => show(el));
    el.addEventListener("pointerleave", () => (tip.hidden = true));
    el.addEventListener("blur", () => (tip.hidden = true));
  });
}

export { METRICS };
