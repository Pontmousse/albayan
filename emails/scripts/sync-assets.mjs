import { cp, mkdir, readdir, readFile, rm } from "node:fs/promises";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const emailRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = join(emailRoot, "assets");
const targets = [
  join(emailRoot, "src", "static"),
  resolve(emailRoot, "..", "frontend", "public", "email"),
];
const assets = [
  "logo.png",
  "header-arch.png",
  "divider.png",
  "pattern.png",
  "footer-corner.png",
  "footer-corner-left.png",
  "footer-corner-right.png",
  "icons/publish.png",
  "icons/read.png",
  "icons/community.png",
  "icons/website.png",
  "icons/email.png",
];
const checkOnly = process.argv.includes("--check");

async function filesUnder(root, directory = root) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await filesUnder(root, path)));
    if (entry.isFile()) files.push(relative(root, path));
  }
  return files.sort();
}

async function assertSourceAssetsExist() {
  await Promise.all(assets.map((asset) => readFile(join(sourceRoot, asset))));
}

async function checkTarget(target) {
  const expected = [...assets].sort();
  const actual = await filesUnder(target);
  if (actual.join("\n") !== expected.join("\n")) {
    console.error(`${relative(emailRoot, target)} has a different asset manifest`);
    return false;
  }

  let matches = true;
  for (const asset of expected) {
    const [source, copy] = await Promise.all([
      readFile(join(sourceRoot, asset)),
      readFile(join(target, asset)),
    ]);
    if (!source.equals(copy)) {
      console.error(`${relative(emailRoot, join(target, asset))} differs from its source`);
      matches = false;
    }
  }
  return matches;
}

async function syncTarget(target) {
  await rm(target, { recursive: true, force: true });
  for (const asset of assets) {
    const destination = join(target, asset);
    await mkdir(dirname(destination), { recursive: true });
    await cp(join(sourceRoot, asset), destination);
  }
}

await assertSourceAssetsExist();

if (checkOnly) {
  const results = await Promise.all(targets.map(checkTarget));
  if (results.every(Boolean)) {
    console.log("Email asset copies match their canonical sources.");
  } else {
    process.exitCode = 1;
  }
} else {
  await Promise.all(targets.map(syncTarget));
  console.log("Synced React Email preview and Next.js public email assets.");
}
