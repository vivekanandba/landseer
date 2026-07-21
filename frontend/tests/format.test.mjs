// Pure formatter / parser tests — Node's built-in runner, no dependencies.
import assert from "node:assert/strict";
import { test } from "node:test";

import { csv, inr, parseVertices, sqft, titlecase, escapeHtml } from "../js/ui.js";

test("inr formats rupees with Cr / L scaling", () => {
  assert.equal(inr(null), "—");
  assert.equal(inr(undefined), "—");
  assert.equal(inr(0), "₹0");
  assert.equal(inr(500), "₹500");
  assert.equal(inr(150000), "₹1.50 L");
  assert.equal(inr(12500000), "₹1.25 Cr");
});

test("sqft formats with thousands separators", () => {
  assert.equal(sqft(12500), "12,500 sqft");
  assert.equal(sqft(null), "—");
});

test("titlecase capitalizes words and de-snakes", () => {
  assert.equal(titlecase("issues_found"), "Issues Found");
  assert.equal(titlecase("north"), "North");
  assert.equal(titlecase(""), "");
});

test("csv trims, drops empties, and handles nullish", () => {
  assert.deepEqual(csv("a, b ,,c"), ["a", "b", "c"]);
  assert.deepEqual(csv(""), []);
  assert.deepEqual(csv(undefined), []);
});

test("parseVertices keeps valid 'lat, lng' lines and drops the rest", () => {
  const out = parseVertices("12.9, 79.1\n12.91,79.11\nnot a point\n13,79");
  assert.deepEqual(out, [
    { lat: 12.9, lng: 79.1 },
    { lat: 12.91, lng: 79.11 },
    { lat: 13, lng: 79 },
  ]);
  assert.deepEqual(parseVertices(""), []);
  assert.deepEqual(parseVertices("one number\n1,2,3"), []);
});

test("escapeHtml neutralizes markup", () => {
  assert.equal(escapeHtml('<b>&"x'), "&lt;b&gt;&amp;&quot;x");
});
