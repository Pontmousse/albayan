import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const emailRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const html = await readFile(resolve(emailRoot, "out", "Welcome.html"), "utf8");

for (const variable of [
  "USER_NAME",
  "LOGIN_URL",
  "SITE_URL",
  "CONTACT_EMAIL",
  "ASSET_BASE_URL",
]) {
  assert.match(html, new RegExp(`\\{\\{\\{${variable}\\}\\}\\}`));
}

for (const asset of [
  "logo.png",
  "header-arch.png",
  "divider.png",
  "footer-corner.png",
  "icons/publish.png",
  "icons/read.png",
  "icons/community.png",
  "icons/website.png",
  "icons/email.png",
]) {
  assert.ok(
    html.includes(`{{{ASSET_BASE_URL}}}/${asset}`),
    `Exported template is missing ${asset}`,
  );
}

assert.ok(!html.includes("/static/"), "Export must not contain preview asset URLs");
assert.ok(
  !html.includes("https://albayan-journal.org/email/"),
  "Export must resolve assets from EMAIL_ASSET_BASE_URL at send time",
);
assert.ok(!html.includes("albayan@gmail.com"), "Legacy contact address found");

console.log("Exported welcome template contains the declared Resend variables.");
