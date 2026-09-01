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

  for (const asset of template.assets) {
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
}

console.log("Exported templates contain their declared Resend variables.");
