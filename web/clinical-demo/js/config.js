/**
 * Demo UI configuration — extend for production:
 * - Set `api.basePath` from a build-time or runtime env (same origin vs dedicated API host).
 * - Add `auth.getHeaders()` and wrap `fetch` in api.js when you have OIDC / API keys.
 * - Flip `features.*` as measurement pipelines (PACS, auto-segmentation) come online.
 */
export const CONFIG = {
  api: {
    basePath: "/api/v1",
    get scoreVersions() {
      return `${this.basePath}/score/versions`;
    },
    get demoNumicFlowFromRecord() {
      return `${this.basePath}/demo/numic-flow-from-record`;
    },
  },
  /** Matches `PatientMeasurementRecord.entry_source` — demo assumes trusted mm from overlay / workstation. */
  measurement: {
    entrySource: "overlay",
    measuredBy: "clinical-demo-ui",
  },
  features: {
    /** Pixel-to-mm is not part of the clinical demo story; keep off until a model + governance ship. */
    experimentalImageUpload: false,
  },
};
