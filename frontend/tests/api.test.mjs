// API-client tests: URL/query building, auth header, body serialization, and
// error normalization — with stubbed fetch + localStorage. No dependencies.
import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { ApiError, api, setBase, setSession } from "../js/api.js";

let calls;
const originalFetch = globalThis.fetch;
const originalLocalStorage = globalThis.localStorage;

function stubLocalStorage() {
  const store = new Map();
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  };
}

// nextResponse: { status, ok, body } — body is the raw text the server returns.
function stubFetch(nextResponse) {
  globalThis.fetch = async (url, opts) => {
    calls.push({ url, opts });
    return {
      status: nextResponse.status,
      ok: nextResponse.ok,
      text: async () => nextResponse.body ?? "",
    };
  };
}

beforeEach(() => {
  calls = [];
  stubLocalStorage();
  setBase("");
  setSession("");
});

afterEach(() => {
  // Restore globals so these stubs can't leak into a shared runtime later.
  globalThis.fetch = originalFetch;
  globalThis.localStorage = originalLocalStorage;
});

test("builds query string, omitting empty params", async () => {
  stubFetch({ status: 200, ok: true, body: "[]" });
  await api.properties({ limit: 2, location: "Thuthikadu", min_price: "" });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/api/v1/properties?limit=2&location=Thuthikadu");
  assert.equal(calls[0].opts.method, "GET");
  assert.equal(calls[0].opts.headers.Authorization, undefined);
});

test("adds bearer session and base URL when configured", async () => {
  setBase("http://api.example");
  setSession("secret");
  stubFetch({ status: 200, ok: true, body: "[]" });
  await api.properties();
  assert.equal(calls[0].url, "http://api.example/api/v1/properties");
  assert.equal(calls[0].opts.headers.Authorization, "Bearer secret");
});

test("serializes POST bodies as JSON with content-type", async () => {
  stubFetch({ status: 201, ok: true, body: '{"id":7}' });
  const created = await api.createProperty({ name: "X" });
  assert.equal(calls[0].opts.method, "POST");
  assert.equal(calls[0].opts.headers["Content-Type"], "application/json");
  assert.equal(calls[0].opts.body, '{"name":"X"}');
  assert.deepEqual(created, { id: 7 });
});

test("normalizes a JSON error body to ApiError(status, detail)", async () => {
  stubFetch({ status: 409, ok: false, body: '{"detail":"already exists"}' });
  await assert.rejects(api.createProperty({ name: "dup" }), (e) => {
    assert.ok(e instanceof ApiError);
    assert.equal(e.status, 409);
    assert.equal(e.message, "already exists");
    return true;
  });
});

test("does not throw a parse error on a non-JSON error body", async () => {
  stubFetch({ status: 502, ok: false, body: "<html>Bad Gateway</html>" });
  await assert.rejects(api.properties(), (e) => {
    assert.ok(e instanceof ApiError);
    assert.equal(e.status, 502);
    assert.equal(e.message, "HTTP 502");
    return true;
  });
});

test("returns null for 204 without reading the body", async () => {
  stubFetch({ status: 204, ok: true, body: "SHOULD-NOT-BE-READ" });
  assert.equal(await api.ready(), null);
});
