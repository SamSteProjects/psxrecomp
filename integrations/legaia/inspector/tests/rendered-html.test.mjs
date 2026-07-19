import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
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

test("server-renders the read-only town01 inspector", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /<title>Legaia Trace — Read-only scene inspector<\/title>/i);
  assert.match(html, /Legaia Trace/);
  assert.match(html, /Actor records/);
  assert.match(html, /Placement projection/);
  assert.match(html, /Metadata-only inspection/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("keeps imported metadata local and the surface read-only", async () => {
  const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  const layout = await readFile(new URL("../app/layout.tsx", import.meta.url), "utf8");
  const packageJson = await readFile(new URL("../package.json", import.meta.url), "utf8");
  assert.match(page, /accept="application\/json,\.json"/);
  assert.match(page, /Nothing is uploaded/);
  assert.match(page, /schema_version === "legaia\.scene-import\.v1"/);
  assert.match(page, /scene\?\.name === "town01"/);
  assert.doesNotMatch(page, /\bfetch\s*\(|XMLHttpRequest|localStorage|sessionStorage|WebSocket/);
  assert.doesNotMatch(page, /write_ram|4370|contentEditable/i);
  assert.doesNotMatch(layout, /codex-preview|_sites-preview/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton|drizzle/);
});
