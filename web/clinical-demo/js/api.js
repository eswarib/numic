import { CONFIG } from "./config.js";

const { header, storageKey } = CONFIG.sandbox;

function readToken() {
  try {
    return localStorage.getItem(storageKey);
  } catch {
    return null;
  }
}

let token = readToken();

function keepToken(value) {
  if (!value || value === token) return;
  token = value;
  try {
    localStorage.setItem(storageKey, value);
  } catch {
    /* private mode: the token lives for this page only */
  }
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function detailText(detail, status) {
  if (!detail) return `Request failed (HTTP ${status})`;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = (d.loc || []).filter((p) => p !== "body").join(" ");
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join("; ");
  }
  return JSON.stringify(detail);
}

async function request(method, path, body) {
  const headers = { Accept: "application/json" };
  if (token) headers[header] = token;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const r = await fetch(`${CONFIG.api.basePath}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  keepToken(r.headers.get(header));
  if (r.status === 204) return null;
  const data = await r.json().catch(() => null);
  if (!r.ok) throw new ApiError(r.status, detailText(data?.detail, r.status));
  return data;
}

export const api = {
  listBabies: () => request("GET", "/demo/babies"),
  getBaby: (id) => request("GET", `/demo/babies/${encodeURIComponent(id)}`),
  addBaby: (body) => request("POST", "/demo/babies", body),
  deleteBaby: (id) => request("DELETE", `/demo/babies/${encodeURIComponent(id)}`),
  addScan: (id, body) => request("POST", `/demo/babies/${encodeURIComponent(id)}/scans`, body),
  deleteScan: (id, scanId) =>
    request("DELETE", `/demo/babies/${encodeURIComponent(id)}/scans/${encodeURIComponent(scanId)}`),
  resetSandbox: () => request("POST", "/demo/sandbox/reset"),
};
