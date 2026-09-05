import assert from "node:assert/strict";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
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
  assert.match(html, /Draft room/);
  assert.match(html, /Career H2H/);
  assert.match(html, /One fixture\. Your tactical call\./);
  assert.doesNotMatch(html, /Every layer has one job|View system design|Architecture/);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site/);
});

test("labels demonstration data and preserves no-login access", async () => {
  const response = await render();
  const html = await response.text();
  assert.match(html, /seeded data/i);
  assert.match(html, /Open league app/);
  assert.match(html, /Explore demo league/);
  assert.match(html, /No affiliation with FPL, FotMob, StatsBomb/);
  assert.match(html, /Run next seed/);
  assert.match(html, /no real match prediction/i);
});

test("server-renders the separate league workspace", async () => {
  const response = await render("/app");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /League Workspace — FFV/);
  assert.match(html, /Career command centre/);
  assert.match(html, /Separate career table/i);
  assert.match(html, /Seeded preview/i);
  assert.match(html, /Immutable event history/i);
  assert.match(html, /Set tactics/i);
  assert.match(html, /Friday · 5:00 PM/i);
});

test("server-renders the reconnectable draft room", async () => {
  const response = await render("/app/draft");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Draft Room — FFV/);
  assert.match(html, /server-authoritative cursor/i);
  assert.match(html, /State rebuilt from accepted picks/i);
  assert.match(html, /Florian Wirtz/);
  assert.match(html, /Reconnect contract/i);
  assert.match(html, /Create one command ID before sending/i);
  assert.match(html, /Reuse that ID for every network retry/i);
  assert.match(html, /45 seconds per pick/i);
});

test("server-renders the blind FAAB workspace without exposing bids", async () => {
  const response = await render("/app/league");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Blind FAAB — FFV/);
  assert.match(html, /YOUR BALANCE/i);
  assert.match(html, /5:00 PM/);
  assert.match(html, /Other bids hidden/i);
  assert.match(html, /Equal amounts use hidden waiver priority/i);
  assert.doesNotMatch(html, /Manager 1 bid|Manager 2 bid/i);
});

test("server-renders the interactive trade state machine", async () => {
  const response = await render("/app/trades");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Trade Room — FFV/);
  assert.match(html, /Build a one-for-one trade/i);
  assert.match(html, /Proposed → accepted → approved/i);
  assert.match(html, /36h/);
  assert.match(html, /checks them again at approval/i);
  assert.match(html, /Roster ownership/i);
});
