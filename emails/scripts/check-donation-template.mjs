import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const html = await readFile(resolve(root, "out/donations/DonationReceived.html"), "utf8");

for (const variable of [
  "AMOUNT_TEXT",
  "DATE_TEXT",
  "SITE_URL",
  "CONTACT_EMAIL",
  "ASSET_BASE_URL",
]) {
  assert.match(html, new RegExp(`\\{\\{\\{${variable}\\}\\}\\}`));
}

assert.ok(!html.includes("DONATION_REFERENCE"));
assert.ok(!html.includes("/static/"));
assert.ok(!/\b(?:Stripe|Resend|FastAPI|Next\.js)\b/i.test(html));
assert.match(html, /خدمات مجلة البيان العلمية متاحة دون مقابل/);
assert.match(html, /ليست إيصالًا ضريبيًا/);

console.log("Donation email template passed export checks.");
