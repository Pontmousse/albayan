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

// Full-width email tables must not also carry horizontal margins: several
// clients count the table's width before its margins and visibly shift/clamp
// the donation cards. The shell owns spacing; the inner card stays at 100%.
assert.ok(!html.includes("margin:10px 34px 18px"));
assert.ok(!html.includes("margin:10px 34px 18px;"));
assert.match(html, /donation-card-shell/);
assert.match(html, /donation-card/);
assert.match(html, /white-space:nowrap/);

console.log("Donation email template passed export checks.");
