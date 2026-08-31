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
    `${template.file} must resolve assets from EMAIL_ASSET_BASE_URL at send time`,
  );
  assert.ok(!html.includes("albayan@gmail.com"), "Legacy contact address found");
}

console.log("Exported templates contain their declared Resend variables.");
