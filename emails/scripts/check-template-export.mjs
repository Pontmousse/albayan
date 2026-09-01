import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const emailRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const templates = [
  {
    file: "Welcome.html",
    variables: [
      "USER_NAME",
      "LOGIN_URL",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: [
      "logo.png",
      "header-arch.png",
      "divider.png",
      "footer-corner.png",
      "icons/publish.png",
      "icons/read.png",
      "icons/community.png",
      "icons/website.png",
      "icons/email.png",
    ],
  },
  {
    file: "AppInvitation.html",
    variables: [
      "INVITATION_URL",
      "RECIPIENT_NAME",
      "RECIPIENT_EMAIL",
      "EXPIRES_TEXT",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: [
      "logo.png",
      "header-arch.png",
      "divider.png",
      "footer-corner.png",
      "icons/website.png",
      "icons/email.png",
    ],
  },
  {
    file: "auth/VerificationCode.html",
    variables: [
      "OTP_CODE",
      "RECIPIENT_EMAIL",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: [
      "logo.png",
      "header-arch.png",
      "divider.png",
      "footer-corner.png",
      "icons/website.png",
      "icons/email.png",
    ],
  },
  {
    file: "auth/PasswordReset.html",
    variables: [
      "OTP_CODE",
      "RECIPIENT_EMAIL",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: [
      "logo.png",
      "header-arch.png",
      "divider.png",
      "footer-corner.png",
      "icons/website.png",
      "icons/email.png",
    ],
  },
  {
    file: "articles/SubmissionReceived.html",
    variables: [
      "ARTICLE_TITLE",
      "ARTICLE_URL",
      "SUBMITTED_TEXT",
      "VERSION_NUMBER",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "articles/NewSubmissionAlert.html",
    variables: [
      "ARTICLE_TITLE",
      "AUTHOR_NAME",
      "ARTICLE_URL",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "articles/EditorAssigned.html",
    variables: [
      "ARTICLE_TITLE",
      "ARTICLE_URL",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "ReviewInvitation.html",
    variables: [
      "ARTICLE_TITLE",
      "ROLE_LABEL",
      "INVITATION_URL",
      "EXPIRES_TEXT",
      "DUE_TEXT",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "ReviewerAssigned.html",
    variables: [
      "ARTICLE_TITLE",
      "REVIEW_URL",
      "DUE_TEXT",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "ReviewReminder.html",
    variables: [
      "ARTICLE_TITLE",
      "REVIEW_URL",
      "DUE_TEXT",
      "REMINDER_TEXT",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "ReviewSubmitted.html",
    variables: [
      "ARTICLE_TITLE",
      "REVIEWER_NAME",
      "REPORT_URL",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "articles/Decision.html",
    variables: [
      "ARTICLE_TITLE",
      "DECISION_TEXT",
      "ARTICLE_URL",
      "NEXT_STEP",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "articles/Published.html",
    variables: [
      "ARTICLE_TITLE",
      "ARTICLE_URL",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
  {
    file: "notifications/UnreadDigest.html",
    variables: [
      "UNREAD_COUNT",
      "NOTIFICATIONS_URL",
      "SITE_URL",
      "CONTACT_EMAIL",
      "ASSET_BASE_URL",
    ],
    assets: ["logo.png", "header-arch.png", "divider.png", "footer-corner.png", "icons/website.png", "icons/email.png"],
  },
];

for (const template of templates) {
  const html = await readFile(resolve(emailRoot, "out", template.file), "utf8");

  for (const variable of template.variables) {
    assert.match(html, new RegExp(`\\{\\{\\{${variable}\\}\\}\\}`));
  }

  const expectedAssets = template.assets.flatMap((asset) =>
    asset === "footer-corner.png"
      ? ["footer-corner-left.png", "footer-corner-right.png"]
      : [asset],
  );

  for (const asset of expectedAssets) {
    assert.ok(
      html.includes(`{{{ASSET_BASE_URL}}}/${asset}`),
      `${template.file} is missing ${asset}`,
    );
  }

  assert.ok(!html.includes("/static/"), `${template.file} contains preview asset URLs`);
  assert.ok(
    !html.includes("https://albayan-journal.org/email/"),
    `${template.file} must resolve assets from ASSET_BASE_URL at send time`,
  );
  assert.ok(!html.includes("albayan@gmail.com"), "Legacy contact address found");
  assert.match(html, /name="viewport"/i, `${template.file} is missing a viewport meta tag`);
  assert.match(html, /max-width:\s*620px/i, `${template.file} is missing mobile CSS`);
  assert.ok(!/transform:\s*scaleX/i.test(html), `${template.file} mirrors an image with CSS`);
  assert.ok(
    !/\b(?:Clerk|Resend|Next\.js|FastAPI)\b/i.test(html),
    `${template.file} exposes an implementation vendor to recipients`,
  );

  for (const variable of template.variables.filter(
    (name) => name.endsWith("_URL") && !["SITE_URL", "ASSET_BASE_URL"].includes(name),
  )) {
    const occurrences = html.split(`{{{${variable}}}}`).length - 1;
    assert.equal(
      occurrences,
      1,
      `${template.file} must render ${variable} only as its single action link`,
    );
  }
}

console.log("Exported templates passed variable, asset, mobile, and link checks.");
