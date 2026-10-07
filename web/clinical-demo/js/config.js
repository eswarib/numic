/**
 * Demo UI configuration (display only — never changes a score; thresholds live in the backend rule-set file).
 */
export const CONFIG = {
  api: {
    basePath: "/api/v1",
  },
  /** Sandbox token header; a header (not a cookie) so the demo also works inside an embedded frame. */
  sandbox: {
    header: "X-Demo-Sandbox",
    storageKey: "numic-demo-sandbox",
  },
  /** Neutral band wording: describes the band, gives no clinical instructions (DEMO-F13). */
  bands: {
    low: { label: "Low", text: "Lower-risk band" },
    moderate: { label: "Moderate", text: "Intermediate-risk band" },
    high: { label: "High", text: "Higher-risk band" },
  },
  concern: {
    none: "None",
    mild: "Mild",
    clear: "Clear",
  },
  /** Default date of birth for a new synthetic baby: this many days before today. */
  newBabyDefaultAgeDays: 7,
  timeZone: "Europe/London",
};
