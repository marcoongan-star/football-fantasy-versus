import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../app/app/ffv-api.ts", import.meta.url), "utf8");

test("development adapter sends the identity contract FastAPI verifies", () => {
  assert.match(source, /"X-FFV-User-Id"/);
  assert.match(source, /"X-FFV-User-Email"/);
  assert.match(source, /"X-FFV-User-Name"/);
  assert.doesNotMatch(source, /"X-User-Id"/);
});

test("commissioner commands use the authenticated league routes", () => {
  assert.match(source, /invite\/rotate/);
  assert.match(source, /invite\/revoke/);
  assert.match(source, /members\/\$\{userId\}\/restore/);
  assert.match(source, /method: "DELETE"/);
  assert.match(source, /\/audit/);
});
