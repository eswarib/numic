import { CONFIG } from "./config.js";

export async function fetchScoreVersions() {
  const response = await fetch(CONFIG.api.scoreVersions);
  if (!response.ok) throw new Error(`score/versions HTTP ${response.status}`);
  return response.json();
}

/**
 * @param {object} body DemoNumicFlowFromRecordRequest
 * @returns {Promise<Response>}
 */
export function postDemoNumicFlow(body) {
  return fetch(CONFIG.api.demoNumicFlowFromRecord, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
