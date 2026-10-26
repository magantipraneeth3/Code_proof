import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ApiError, createClient } from "./client.ts";
import { formatBytes, formatDate, metricLabel, modelSummary, statusLabel } from "../utils/format.ts";

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

describe("api client", () => {
  it("sends bearer token and JSON body", async () => {
    let seen: any;
    const c = createClient({
      baseUrl: "http://x/api", getToken: () => "tok",
      fetchImpl: (async (url: any, init: any) => { seen = { url, init }; return json(200, { ok: true }); }) as any,
    });
    assert.deepEqual(await c.post("/p", { a: 1 }), { ok: true });
    assert.equal(seen.url, "http://x/api/p");
    assert.equal(seen.init.headers.Authorization, "Bearer tok");
    assert.equal(seen.init.body, '{"a":1}');
  });

  it("omits Authorization when logged out", async () => {
    let seen: any;
    const c = createClient({ baseUrl: "", getToken: () => null,
      fetchImpl: (async (_u: any, init: any) => { seen = init; return json(200, {}); }) as any });
    await c.get("/x");
    assert.equal(seen.headers.Authorization, undefined);
  });

  it("turns API errors into ApiError with the server message", async () => {
    const c = createClient({ baseUrl: "", getToken: () => null,
      fetchImpl: (async () => json(404, { error: "http_404", message: "Submission not found.", request_id: "r" })) as any });
    await assert.rejects(c.get("/x"), (e: any) => e instanceof ApiError && e.status === 404 && e.message === "Submission not found.");
  });

  it("calls onUnauthorized on 401", async () => {
    let called = false;
    const c = createClient({ baseUrl: "", getToken: () => "t", onUnauthorized: () => { called = true; },
      fetchImpl: (async () => json(401, { message: "Not authenticated." })) as any });
    await assert.rejects(c.get("/x"));
    assert.equal(called, true);
  });

  it("handles 204 and non-JSON error bodies and network failure", async () => {
    const ok = createClient({ baseUrl: "", getToken: () => null, fetchImpl: (async () => new Response(null, { status: 204 })) as any });
    assert.equal(await ok.del("/x"), undefined);
    const html = createClient({ baseUrl: "", getToken: () => null, fetchImpl: (async () => new Response("<html>", { status: 502 })) as any });
    await assert.rejects(html.get("/x"), (e: any) => e.status === 502 && /502/.test(e.message));
    const down = createClient({ baseUrl: "", getToken: () => null, fetchImpl: (async () => { throw new TypeError("fail"); }) as any });
    await assert.rejects(down.get("/x"), (e: any) => e.status === 0 && e.code === "network_error");
  });

  it("does not set a JSON content-type for FormData", async () => {
    let seen: any;
    const c = createClient({ baseUrl: "", getToken: () => null,
      fetchImpl: (async (_u: any, init: any) => { seen = init; return json(200, {}); }) as any });
    const f = new FormData(); f.set("a", "b");
    await c.post("/u", f);
    assert.equal(seen.headers["Content-Type"], undefined);
    assert.ok(seen.body instanceof FormData);
  });
});

describe("format helpers", () => {
  it("labels statuses honestly", () => {
    assert.equal(statusLabel("unsupported_language"), "Language not supported yet");
    assert.equal(statusLabel(null), "Not analyzed");
    assert.equal(statusLabel("weird"), "weird");
  });
  it("never reports a prediction without an available model and a probability", () => {
    const base = { authorship_assessment: "inconclusive" };
    assert.match(modelSummary({ ...base, model_status: "unavailable", probability: null }), /No authorship prediction/);
    assert.match(modelSummary({ ...base, model_status: "available", probability: null }), /No authorship prediction/);
  });
  it("formats labels and dates", () => {
    assert.equal(metricLabel("max_nesting_depth"), "Max nesting depth");
    assert.equal(formatDate(null), "—");
    assert.equal(formatDate("not a date"), "not a date");
  });
  it("formats byte counts at the analysis limit", () => {
    assert.equal(formatBytes(0), "0 B");
    assert.equal(formatBytes(1250), "1.3 KB");
    assert.equal(formatBytes(1_000_000), "1.0 MB");
  });
});
