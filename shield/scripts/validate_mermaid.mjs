#!/usr/bin/env node
// Validate ONE mermaid diagram read from stdin with the real parser.
// Exit codes: 0 = valid, 1 = syntax error (message on stderr),
//             2 = backend/setup failure (caller should fall back).
// Syntax-only: mermaid.parse() needs a DOM (jsdom) but NOT headless Chromium.
//
// Module resolution: this script is launched via
//   npx --yes --package mermaid@10 --package jsdom node validate_mermaid.mjs
// On modern npm, npx installs the packages into a cache dir and only exposes
// that dir's node_modules/.bin on PATH — it does NOT set NODE_PATH, and ESM
// `import` of a bare specifier ignores NODE_PATH anyway. So we derive npx's
// node_modules directory from PATH and import the packages by absolute file URL.
import { createRequire } from "module";
import { pathToFileURL } from "url";
import path from "path";

function resolveNpxNodeModules() {
  for (const dir of (process.env.PATH || "").split(path.delimiter)) {
    if (dir.endsWith(path.join("node_modules", ".bin")) && dir.includes("_npx")) {
      return path.dirname(dir);
    }
  }
  return null;
}

let mermaid;
try {
  const nm = resolveNpxNodeModules();
  // createRequire from the npx node_modules dir resolves both packages there;
  // fall back to plain bare specifiers if PATH-derivation failed (e.g. a local
  // install where the packages are resolvable normally).
  const req = nm ? createRequire(pathToFileURL(nm + path.sep)) : createRequire(import.meta.url);
  const resolve = (spec) => {
    try { return pathToFileURL(req.resolve(spec)).href; } catch { return spec; }
  };
  const { JSDOM } = await import(resolve("jsdom"));
  const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  if (!("navigator" in globalThis)) {
    Object.defineProperty(globalThis, "navigator", {
      value: dom.window.navigator,
      configurable: true,
    });
  }
  mermaid = (await import(resolve("mermaid"))).default;
  mermaid.initialize({ startOnLoad: false });
} catch (e) {
  process.stderr.write("backend-setup-failure: " + (e?.message ?? e));
  process.exit(2);
}

let input = "";
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) input += chunk;

try {
  await mermaid.parse(input);
  process.exit(0);
} catch (err) {
  process.stderr.write(String(err?.message ?? err));
  process.exit(1);
}
