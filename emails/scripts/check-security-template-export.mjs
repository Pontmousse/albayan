import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const emailRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const templates = [
  "auth/AccountLocked.html",
  "auth/PasswordChanged.html",
  "auth/PasswordRemoved.html",
  "auth/PrimaryEmailChanged.html",
  "auth/NewDeviceSignIn.html",
];

const variables = [
  "RECIPIENT_EMAIL",
  "DATE_TEXT",
  "SITE_URL",
  "CONTACT_EMAIL",
  "ASSET_BASE_URL",
];

for (const file of templates) {
  const html = await readFile(resolve(emailRoot, "out", file), "utf8");

  for (const variable of variables) {
    assert.match(
      html,
      new RegExp(`\\{\\{\\{${variable}\\}\\}\\}`),
      `${file} is missing ${variable}`,
    );
  }

  for (const asset of [
    "logo.png",
    "header-arch.png",
    "divider.png",
    "footer-corner-left.png",
    "footer-corner-right.png",
    "icons/website.png",
    "icons/email.png",
  ]) {
    assert.ok(
      html.includes(`{{{ASSET_BASE_URL}}}/${asset}`),
      `${file} is missing ${asset}`,
    );
  }

  assert.ok(!html.includes("/static/"), `${file} contains preview asset URLs`);
  assert.ok(!/\b(?:Clerk|Resend|Next\.js|FastAPI)\b/i.test(html), `${file} exposes an implementation vendor`);
  assert.match(html, /name="viewport"/i, `${file} is missing viewport metadata`);
  assert.match(html, /max-width:\s*620px/i, `${file} is missing mobile CSS`);
  assert.match(
    html,
    /<strong[^>]*>\s*\{\{\{RECIPIENT_EMAIL\}\}\}\s*<\/strong\s*>/is,
    `${file} must render RECIPIENT_EMAIL in bold`,
  );

  for (const variable of ["SITE_URL", "CONTACT_EMAIL"]) {
    const occurrences = html.split(`{{{${variable}}}}`).length - 1;
    assert.equal(
      occurrences,
      1,
      `${file} must use ${variable} only for its footer icon link`,
    );
  }
}

console.log("Exported Clerk security templates passed variable, asset, mobile, and vendor checks.");
