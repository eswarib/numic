import { CONFIG } from "./config.js";

/**
 * @param {"prior"|"current"} which
 * @returns {{ vi_mm: number, ahw_mm: number, tod_mm: number, vi_percentile: number, measured_at: string } | null}
 */
export function readScan(which) {
  const vi = parseFloat(document.getElementById(`vi-${which}`).value);
  const ahw = parseFloat(document.getElementById(`ahw-${which}`).value);
  const tod = parseFloat(document.getElementById(`tod-${which}`).value);
  const pct = parseFloat(document.getElementById(`pct-${which}`).value);
  const dt = document.getElementById(`dt-${which}`).value;
  if ([vi, ahw, tod, pct].some((x) => Number.isNaN(x))) return null;
  return { vi_mm: vi, ahw_mm: ahw, tod_mm: tod, vi_percentile: pct, measured_at: dt };
}

function toIsoZ(dtLocal) {
  if (!dtLocal) return new Date().toISOString();
  const d = new Date(dtLocal);
  if (Number.isNaN(d.getTime())) return new Date().toISOString();
  return d.toISOString();
}

/**
 * Build API patient measurement record. Production UI will add persistence IDs and provenance.
 * @param {ReturnType<typeof readScan>} rowData
 * @param {{ isCurrent: boolean }} opts
 */
export function buildRecord(rowData, opts) {
  const ref = parseFloat(document.getElementById("viP97Ref").value);
  const viRef = Number.isNaN(ref) ? null : ref;
  const externalRef = document.getElementById("externalRef").value.trim() || "DEMO";
  const ga = document.getElementById("gaWeeks").value;
  const gaWeeks = ga === "" ? null : parseFloat(ga);
  const notes =
    opts?.isCurrent && document.getElementById("clinicalNotes").value.trim()
      ? document.getElementById("clinicalNotes").value.trim()
      : null;

  return {
    patient: {
      external_ref: externalRef,
      gestational_age_weeks: gaWeeks,
    },
    context: {
      measured_at: toIsoZ(rowData.measured_at),
      measured_by: CONFIG.measurement.measuredBy,
      clinical_notes: notes,
    },
    measurements: {
      vi_mm: rowData.vi_mm,
      ahw_mm: rowData.ahw_mm,
      tod_mm: rowData.tod_mm,
      vi_percentile: rowData.vi_percentile,
      vi_p97_reference_mm: viRef,
    },
    entry_source: CONFIG.measurement.entrySource,
  };
}

/** @returns {{ concern: "none"|"mild"|"clear" }} */
export function clinicalPayload() {
  const sel = document.querySelector('input[name="clinicalConcern"]:checked');
  const v = sel?.value ?? "none";
  if (v === "mild" || v === "clear") return { concern: v };
  return { concern: "none" };
}
