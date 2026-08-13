import assert from "node:assert/strict";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the public FFV recruiter demo", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /<title>FFV — Football Fantasy Versus<\/title>/i);
  assert.match(html, /Fantasy football that/);
  assert.match(html, /Recruiter demo · seeded data/);
  assert.match(html, /The Gegenpress Society/);
  assert.doesNotMatch(html, /Every layer has one job|View system design|Architecture/);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site/);
});

test("labels demonstration data and preserves no-login access", async () => {
  const response = await render();
  const html = await response.text();
  assert.match(html, /seeded data/i);
  assert.match(html, /Join a league/);
  assert.match(html, /Explore demo league/);
  assert.match(html, /No affiliation with FPL, FotMob, StatsBomb/);
});
