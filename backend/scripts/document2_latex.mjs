#!/usr/bin/env node
/**
 * Reads BuTeX document.json from stdin, writes full Arabic XeLaTeX to stdout.
 * Resolves @drghaliasri/butex from backend/node_modules or frontend/node_modules.
 */
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const candidates = [
  path.resolve(here, "../node_modules/@drghaliasri/butex/dist/document2.mjs"),
  path.resolve(here, "../../frontend/node_modules/@drghaliasri/butex/dist/document2.mjs"),
];
const modPath = candidates.find((p) => existsSync(p));
if (!modPath) {
  console.error(
    "document2_latex: @drghaliasri/butex not found (install in backend/ or frontend/)",
  );
  process.exit(1);
}

const { fromDocumentJson2, document2Latex } = await import(
  pathToFileURL(modPath).href
);

const chunks = [];
for await (const chunk of process.stdin) {
  chunks.push(chunk);
}
const raw = Buffer.concat(chunks).toString("utf8").trim();
if (!raw) {
  console.error("document2_latex: empty stdin");
  process.exit(1);
}

let json;
try {
  json = JSON.parse(raw);
} catch (err) {
  console.error(`document2_latex: invalid JSON: ${err.message}`);
  process.exit(1);
}

try {
  const doc = fromDocumentJson2(json);
  const tex = document2Latex(doc);
  process.stdout.write(tex);
} catch (err) {
  console.error(`document2_latex: export failed: ${err.message}`);
  process.exit(1);
}
