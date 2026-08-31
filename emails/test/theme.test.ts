import assert from "node:assert/strict";
import test from "node:test";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  emailAssetUrl,
  resendTemplateVariable,
} from "../src/_components/theme.ts";

test("builds nested assets from a normalized HTTPS base URL", () => {
  assert.equal(
    emailAssetUrl("https://cdn.example.com/email///", "icons/publish.png"),
    "https://cdn.example.com/email/icons/publish.png",
  );
});

test("builds production URLs from the Resend template placeholder", () => {
  assert.equal(
    emailAssetUrl(ASSET_BASE_URL_PLACEHOLDER, "logo.png"),
    "{{{ASSET_BASE_URL}}}/logo.png",
  );
  assert.equal(resendTemplateVariable("LOGIN_URL"), "{{{LOGIN_URL}}}");
});

test("allows local HTTP only for React Email preview", () => {
  assert.equal(
    emailAssetUrl("http://localhost:3001/static/", "icons/read.png"),
    "http://localhost:3001/static/icons/read.png",
  );
  assert.throws(
    () => emailAssetUrl("http://cdn.example.com/email", "logo.png"),
    /absolute HTTPS URL, or a local preview URL/,
  );
});

test("rejects missing and relative asset base URLs", () => {
  assert.throws(
    () => emailAssetUrl(undefined, "logo.png"),
    /Email asset base URL/,
  );
  assert.throws(
    () => emailAssetUrl("/email", "logo.png"),
    /Email asset base URL/,
  );
});

test("rejects invalid Resend variable names", () => {
  assert.throws(
    () => resendTemplateVariable("not-valid"),
    /Invalid Resend template variable/,
  );
});
