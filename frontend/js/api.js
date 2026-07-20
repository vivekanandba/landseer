// Typed-ish API client for the Landseer backend.
// Base URL and bearer token are configurable and persisted in localStorage, so
// the same static bundle works same-origin (served by the API) or against a
// remote host. Auth is optional (the API is open unless LANDSEER_API_TOKEN is set).

const LS_BASE = "landseer_api_base";
const LS_TOKEN = "landseer_api_token";

export function getBase() {
  return localStorage.getItem(LS_BASE) || "";
}
export function setBase(v) {
  localStorage.setItem(LS_BASE, v || "");
}
export function getToken() {
  return localStorage.getItem(LS_TOKEN) || "";
}
export function setToken(v) {
  localStorage.setItem(LS_TOKEN, v || "");
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

async function request(path, opts = {}) {
  const headers = { Accept: "application/json", ...(opts.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";

  let resp;
  try {
    resp = await fetch(getBase() + path, {
      method: opts.method || "GET",
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    });
  } catch (e) {
    throw new ApiError(0, `Network error: ${e.message}`);
  }

  if (resp.status === 204) return null;
  const text = await resp.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      // Non-JSON body (e.g. an HTML 502 from a proxy). Keep the raw text so the
      // error still carries the status rather than a parse exception.
      if (!resp.ok) throw new ApiError(resp.status, `HTTP ${resp.status}`);
      throw new ApiError(resp.status, "Unexpected non-JSON response");
    }
  }
  if (!resp.ok) {
    const detail =
      (data && (data.detail || (data.error && data.error.message))) || `HTTP ${resp.status}`;
    throw new ApiError(resp.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export const api = {
  health: () => request("/health"),
  ready: () => request("/ready"),

  properties: (params = {}) => request("/api/v1/properties" + qs(params)),
  property: (id) => request(`/api/v1/properties/${id}`),
  createProperty: (payload) => request("/api/v1/properties", { method: "POST", body: payload }),
  updateProperty: (id, payload) =>
    request(`/api/v1/properties/${id}`, { method: "PATCH", body: payload }),
  addSubdivision: (id, payload) =>
    request(`/api/v1/properties/${id}/subdivisions`, { method: "POST", body: payload }),
  addNeighbor: (id, payload) =>
    request(`/api/v1/properties/${id}/neighbors`, { method: "POST", body: payload }),
  addBoundary: (id, payload) =>
    request(`/api/v1/properties/${id}/boundary`, { method: "POST", body: payload }),
  documents: (id) => request(`/api/v1/properties/${id}/documents`),
  uploadDocument: (id, payload) =>
    request(`/api/v1/properties/${id}/documents`, { method: "POST", body: payload }),
  mapGeojson: (id) => request(`/api/v1/properties/${id}/map.geojson`),

  recommendations: (pref, includeDisqualified = true) =>
    request(
      `/api/v1/preferences/${encodeURIComponent(pref)}/recommendations` +
        qs({ include_disqualified: includeDisqualified }),
    ),

  notifications: (params = {}) => request("/api/v1/notifications" + qs(params)),

  brokers: (params = {}) => request("/api/v1/brokers" + qs(params)),
  createBroker: (payload) => request("/api/v1/brokers", { method: "POST", body: payload }),
  linkBroker: (brokerId, propertyId, payload) =>
    request(`/api/v1/brokers/${brokerId}/properties/${propertyId}`, {
      method: "POST",
      body: payload,
    }),
  brokerPerformance: (id) => request(`/api/v1/brokers/${id}/performance`),

  createPreference: (payload) =>
    request("/api/v1/preferences", { method: "POST", body: payload }),

  comparison: (name) => request(`/api/v1/comparisons/${encodeURIComponent(name)}`),
  createComparison: (name, propertyIds) =>
    request("/api/v1/comparisons", { method: "POST", body: { name, property_ids: propertyIds } }),
  comparisonTable: (name) => request(`/api/v1/comparisons/${encodeURIComponent(name)}/table`),
  comparisonFeatures: (name) =>
    request(`/api/v1/comparisons/${encodeURIComponent(name)}/features`),
  comparisonInvestment: (name) =>
    request(`/api/v1/comparisons/${encodeURIComponent(name)}/investment`),
};

function qs(params) {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  if (!entries.length) return "";
  return "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join("&");
}
