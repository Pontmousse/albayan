import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");

const page = read("src/app/daam-al-bayan/page.tsx");
const checkout = read("src/components/donations/donation-checkout.tsx");
const status = read("src/components/donations/donation-status.tsx");
const nav = read("src/components/main-nav.tsx");
const navConfig = read("src/lib/nav-config.ts");
const quranicOpening = read("src/components/journal/quranic-opening.tsx");
const api = read("src/lib/donations.ts");


test("donation page keeps the free-services and editorial-independence promise", () => {
  assert.match(page, /خدمات مجلة البيان العلمية متاحة دون مقابل/);
  assert.match(page, /لا تؤثر بأي صورة في التقديم أو التحكيم أو القرار التحريري أو النشر/);
  assert.match(page, /رَبِّ زِدْنِي عِلْمًا/);
  assert.match(page, /سورة طه: ١١٤/);
});


test("donation support is prominent in desktop and mobile navigation", () => {
  assert.match(navConfig, /href: "\/daam-al-bayan"/);
  assert.match(navConfig, /label: "دعم البيان"/);
  assert.match(nav, /<SupportNavLink mobile onClick=\{close\} \/>/);
  assert.match(nav, /<SupportNavLink \/>/);
});


test("landing Quran verses use the same display Arabic font as the donation verse", () => {
  assert.match(
    quranicOpening,
    /<blockquote[\s\S]*?fontFamily: "var\(--font-display-ar\), serif"/,
  );
});


test("checkout uses secure Arabic payment controls without raw card inputs", () => {
  assert.match(checkout, /https:\/\/js\.stripe\.com\/dahlia\/stripe\.js/);
  assert.match(checkout, /locale: "ar"/);
  assert.match(checkout, /initCheckoutElementsSdk/);
  assert.match(checkout, /createPaymentElement/);
  assert.match(checkout, /loadActions/);
  assert.match(checkout, /actionsRef\.current\.confirm/);
  assert.doesNotMatch(checkout, /name=["']card_number["']/);
  assert.doesNotMatch(checkout, /CVC.*input/i);
  assert.doesNotMatch(checkout, /مساهمة اختيارية لمرة واحدة/);
  assert.doesNotMatch(checkout, /تديرها Stripe/);
  assert.match(checkout, /حقول آمنة ومشفّرة/);
});


test("donation status copy stays clear and non-technical", () => {
  assert.match(status, /جارٍ التحقق من عملية الدفع/);
  assert.doesNotMatch(status, /تثبيت نتيجة الدفع/);
  assert.doesNotMatch(status, /وصلتَ إلى صفحة العودة/);
  assert.doesNotMatch(status, /الإشعار الموثوق/);
});


test("donation client calls only the public donation API and maps failures to Arabic copy", () => {
  assert.match(api, /\/api\/v1\/public\/donations\/checkout-session/);
  assert.match(api, /\/api\/v1\/public\/donations\/session\//);
  assert.match(api, /apiErrorMessage/);
  assert.doesNotMatch(checkout, /result\.error\.message/);
});
