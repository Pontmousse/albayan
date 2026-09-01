import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const signup = readFileSync(resolve("src/app/tasjil/page.tsx"), "utf8");
const adminApi = readFileSync(resolve("src/lib/api/admin.ts"), "utf8");
const adminUsers = readFileSync(resolve("src/app/admin/mustakhdimin/page.tsx"), "utf8");

assert.match(signup, /searchParams\.get\("__clerk_ticket"\)/);
assert.match(signup, /signUp\s*\.\s*ticket\(/);
assert.match(signup, /signUp\.password\(/);
assert.match(signup, /unsafeMetadata:\s*\{\s*albayan_gender:\s*gender\s*\}/);
assert.match(signup, /<GenderIconSelector/);
assert.match(signup, /id="clerk-captcha"/);
assert.match(adminApi, /\/api\/v1\/admin\/invitations/);
assert.match(adminApi, /revoke/);
assert.match(adminUsers, /دعوة مستخدم جديد/);
assert.match(adminUsers, /full_name:\s*normalizedName/);
assert.match(adminUsers, /gender:\s*invitedGender/);
assert.match(adminUsers, /<GenderIconSelector/);

console.log("Clerk invitation sign-up wiring checks passed.");
