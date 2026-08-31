import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const signup = await readFile("src/app/tasjil/page.tsx", "utf8");
const signin = await readFile("src/app/tawajjuh/page.tsx", "utf8");
const recovery = await readFile("src/app/istirja/page.tsx", "utf8");
const codeForm = await readFile("src/components/email-code-form.tsx", "utf8");
const deletionCard = await readFile(
  "src/components/settings/account-deletion-request-card.tsx",
  "utf8",
);

assert.match(signup, /verifyEmailCode/);
assert.match(signup, /sendEmailCode/);
assert.match(signup, /EmailCodeForm/);
assert.match(signup, /signUp\.password\(\{\s*emailAddress:/);
assert.match(signup, /signUp\.ticket\(/);
assert.match(signup, /id="clerk-captcha"/);

assert.match(signin, /href="\/istirja"/);
assert.match(signin, /signIn\.password/);

assert.match(recovery, /resetPasswordEmailCode\.sendCode/);
assert.match(recovery, /resetPasswordEmailCode\.verifyCode/);
assert.match(recovery, /resetPasswordEmailCode\.submitPassword/);
assert.match(recovery, /EmailCodeForm/);

assert.match(codeForm, /codeLength\?/);
assert.doesNotMatch(codeForm, /maxLength=\{6\}|minLength=\{6\}/);

assert.match(deletionCard, /useReverification/);
assert.match(deletionCard, /\/api\/v1\/users\/me\/deletion-request/);

console.log("Auth email and deletion request wiring checks passed.");
