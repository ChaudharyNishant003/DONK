// Capture full-page screenshots of a static DONK web build for visual comparison.
//
//   node tools/ui-ref/capture.mjs <static-dir> <out-dir> [route-filter]
//
// Every capture uses the same conditions so two builds can be compared pixel by pixel:
// 375x812 phone viewport, Asia/Kolkata, en-IN, a frozen clock, reduced motion and a
// fresh browser profile (empty local database).
import { createServer } from "node:http";
import { readFile, mkdir, stat } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

export const ROUTES = [
  ["root", "/"],
  ["today", "/today/"],
  ["talk", "/talk/"],
  ["life", "/life/"],
  ...["work", "task", "meeting", "idea", "promise", "money", "health", "people", "misc"].map(
    (d) => [`life-${d}`, `/life/${d}/`],
  ),
  ["settings", "/settings/"],
  ["gallery", "/gallery/"],
  ["not-found", "/does-not-exist/"],
];

export const FROZEN_NOW = new Date("2026-10-07T09:30:00+05:30");

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".txt": "text/plain; charset=utf-8",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".wasm": "application/wasm",
  ".png": "image/png",
};

export function serve(root) {
  const server = createServer(async (req, res) => {
    let path = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let file = join(root, path);
    try {
      if ((await stat(file)).isDirectory()) file = join(file, "index.html");
    } catch {
      file = join(root, "404.html");
      res.statusCode = 404;
    }
    try {
      const body = await readFile(file);
      res.setHeader("content-type", TYPES[extname(file)] ?? "application/octet-stream");
      res.end(body);
    } catch {
      res.statusCode = 404;
      res.end("not found");
    }
  });
  return new Promise((ok) => server.listen(0, "127.0.0.1", () => ok(server)));
}

export async function capture(staticDir, outDir, filter) {
  const root = resolve(staticDir);
  await mkdir(outDir, { recursive: true });
  const server = await serve(root);
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();
  const shots = [];
  try {
    for (const scheme of ["light", "dark"]) {
      for (const [name, route] of ROUTES) {
        if (filter && !name.includes(filter)) continue;
        const context = await browser.newContext({
          viewport: { width: 375, height: 812 },
          deviceScaleFactor: 1,
          locale: "en-IN",
          timezoneId: "Asia/Kolkata",
          colorScheme: scheme,
          reducedMotion: "reduce",
        });
        const page = await context.newPage();
        await page.clock.setFixedTime(FROZEN_NOW);
        await page.goto(base + route, { waitUntil: "networkidle" });
        await page.waitForTimeout(1500);
        const file = join(outDir, `${name}-${scheme}.png`);
        await page.screenshot({ path: file, fullPage: true });
        shots.push(file);
        await context.close();
      }
    }
  } finally {
    await browser.close();
    server.close();
  }
  return shots;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [staticDir, outDir, filter] = process.argv.slice(2);
  if (!staticDir || !outDir) {
    console.error("usage: node tools/ui-ref/capture.mjs <static-dir> <out-dir> [route-filter]");
    process.exit(2);
  }
  const shots = await capture(staticDir, outDir, filter);
  console.log(`captured ${shots.length} screenshots into ${outDir}`);
}
