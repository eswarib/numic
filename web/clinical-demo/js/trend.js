/**
 * Scan trend chart — plots VI / AHW / TOD (mm) across prior → current.
 * Pure SVG; no chart library.
 */

const SERIES = [
  { key: "vi_mm", label: "VI", color: "#2563eb" },
  { key: "ahw_mm", label: "AHW", color: "#0d9488" },
  { key: "tod_mm", label: "TOD", color: "#c2410c" },
];

function formatTick(d) {
  if (!d) return "";
  const dt = new Date(d);
  if (Number.isNaN(dt.getTime())) return String(d);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(dt.getDate())}/${pad(dt.getMonth() + 1)} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
}

/**
 * @param {Array<{ label: string, measured_at?: string, vi_mm: number, ahw_mm: number, tod_mm: number }>} points
 * @param {{ viRef?: number | null }} opts
 */
export function renderTrendChart(points, opts = {}) {
  const host = document.getElementById("trendChart");
  const empty = document.getElementById("trendEmpty");
  if (!host) return;

  const usable = (points || []).filter(
    (p) =>
      p &&
      [p.vi_mm, p.ahw_mm, p.tod_mm].every((x) => typeof x === "number" && !Number.isNaN(x)),
  );

  if (!usable.length) {
    host.innerHTML = "";
    if (empty) empty.hidden = false;
    return;
  }
  if (empty) empty.hidden = true;

  const w = host.clientWidth || 480;
  const h = host.clientHeight || 160;
  const pad = { top: 12, right: 14, bottom: 28, left: 36 };
  const plotW = Math.max(40, w - pad.left - pad.right);
  const plotH = Math.max(40, h - pad.top - pad.bottom);

  const values = usable.flatMap((p) => [p.vi_mm, p.ahw_mm, p.tod_mm]);
  const viRef = opts.viRef != null && !Number.isNaN(opts.viRef) ? opts.viRef : null;
  if (viRef != null) values.push(viRef);

  let yMin = Math.min(...values);
  let yMax = Math.max(...values);
  if (yMin === yMax) {
    yMin = Math.max(0, yMin - 2);
    yMax = yMax + 2;
  }
  const yPad = (yMax - yMin) * 0.12;
  yMin = Math.max(0, yMin - yPad);
  yMax = yMax + yPad;

  const n = usable.length;
  const xAt = (i) => (n === 1 ? pad.left + plotW / 2 : pad.left + (i / (n - 1)) * plotW);
  const yAt = (v) => pad.top + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

  const yTicks = 4;
  const grid = [];
  for (let i = 0; i <= yTicks; i++) {
    const v = yMin + ((yMax - yMin) * i) / yTicks;
    const y = yAt(v);
    grid.push(
      `<line x1="${pad.left}" y1="${y}" x2="${pad.left + plotW}" y2="${y}" stroke="#e2e8f0" stroke-width="1"/>` +
        `<text x="${pad.left - 6}" y="${y + 3}" text-anchor="end" class="trend-tick">${v.toFixed(1)}</text>`,
    );
  }

  const paths = SERIES.map((s) => {
    const d = usable
      .map((p, i) => `${i === 0 ? "M" : "L"}${xAt(i).toFixed(1)},${yAt(p[s.key]).toFixed(1)}`)
      .join(" ");
    const dots = usable
      .map(
        (p, i) =>
          `<circle cx="${xAt(i)}" cy="${yAt(p[s.key])}" r="3.5" fill="${s.color}" stroke="#fff" stroke-width="1.5">` +
          `<title>${s.label}: ${p[s.key]} mm (${p.label})</title></circle>`,
      )
      .join("");
    return (
      `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>` +
      dots
    );
  }).join("");

  let refLine = "";
  if (viRef != null) {
    const y = yAt(viRef);
    refLine =
      `<line x1="${pad.left}" y1="${y}" x2="${pad.left + plotW}" y2="${y}" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 3"/>` +
      `<text x="${pad.left + plotW - 2}" y="${y - 4}" text-anchor="end" class="trend-ref">VI ref ${viRef} mm</text>`;
  }

  const xLabels = usable
    .map((p, i) => {
      const x = xAt(i);
      const when = formatTick(p.measured_at);
      return (
        `<text x="${x}" y="${h - 12}" text-anchor="middle" class="trend-xlabel">${p.label}</text>` +
        (when ? `<text x="${x}" y="${h - 2}" text-anchor="middle" class="trend-xsub">${when}</text>` : "")
      );
    })
    .join("");

  host.innerHTML =
    `<svg viewBox="0 0 ${w} ${h}" width="100%" height="100%" role="img" aria-label="Measurement trend across scans">` +
    `<rect x="0" y="0" width="${w}" height="${h}" fill="transparent"/>` +
    grid.join("") +
    refLine +
    paths +
    xLabels +
    `</svg>`;
}

/** Read form values and redraw. */
export function refreshTrendFromForm() {
  const includePrior = document.getElementById("includeProgression")?.checked ?? true;
  const points = [];

  const read = (which, label) => {
    const vi = parseFloat(document.getElementById(`vi-${which}`).value);
    const ahw = parseFloat(document.getElementById(`ahw-${which}`).value);
    const tod = parseFloat(document.getElementById(`tod-${which}`).value);
    const dt = document.getElementById(`dt-${which}`).value;
    if ([vi, ahw, tod].some((x) => Number.isNaN(x))) return null;
    return { label, measured_at: dt, vi_mm: vi, ahw_mm: ahw, tod_mm: tod };
  };

  if (includePrior) {
    const prior = read("prior", "Prior");
    if (prior) points.push(prior);
  }
  const current = read("current", "Current");
  if (current) points.push(current);

  const ref = parseFloat(document.getElementById("viP97Ref")?.value);
  renderTrendChart(points, { viRef: Number.isNaN(ref) ? null : ref });
}
