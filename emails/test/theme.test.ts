import assert from "node:assert/strict";
import test from "node:test";
import {
  ASSET_BASE_URL_PLACEHOLDER,
  emailAssetUrl,
} from "../src/_components/theme.ts";

test("normalizes all trailing slashes on an HTTPS asset base URL", () => {
  assert.equal(
    emailAssetUrl("https://cdn.example.com/email///", "logo.png"),
    "https://cdn.example.com/email/logo.png",
  );
});

test("preserves nested asset paths", () => {
  assert.equal(
    emailAssetUrl("https://cdn.example.com/email", "icons/publish.png"),
    "https://cdn.example.com/email/icons/publish.png",
  );
});

test("accepts the production ASSET_BASE_URL placeholder", () => {
  assert.equal(
    emailAssetUrl(ASSET_BASE_URL_PLACEHOLDER, "icons/publish.png"),
    "{{{ASSET_BASE_URL}}}/icons/publish.png",
  );
});

test("rejects a missing public base URL instead of emitting a relative URL", () => {
  assert.throws(
    () => emailAssetUrl(undefined, "logo.png"),
    /require a public ASSET_BASE_URL/,
  );
});

test("supports an explicitly configured local preview base URL", () => {
  assert.equal(
    emailAssetUrl(undefined, "icons/publish.png", {
      previewBaseUrl: "http://localhost:3001/static/",
    }),
    "http://localhost:3001/static/icons/publish.png",
  );
});

test("rejects non-HTTPS public asset base URLs", () => {
  assert.throws(
    () => emailAssetUrl("http://cdn.example.com/email", "logo.png"),
    /absolute HTTPS URL/,
  );
});
