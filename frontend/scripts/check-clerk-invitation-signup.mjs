import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const signup = readFileSync(resolve("src/app/tasjil/page.tsx"), "utf8");
const adminApi = readFileSync(resolve("src/lib/api/admin.ts"), "utf8");
const adminUsers = readFileSync(resolve("src/app/admin/mustakhdimin/page.tsx"), "utf8");

assert.match(signup, /searchParams\.get\("__clerk_ticket"\)/);
assert.match(signup, /signUp\.ticket\(/);
assert.match(signup, /signUp\.password\(\{\s*emailAddress:/);
assert.match(signup, /id="clerk-captcha"/);
assert.match(adminApi, /\/api\/v1\/admin\/invitations/);
assert.match(adminApi, /revoke/);
assert.match(adminUsers, /دعوة مستخدم جديد/);

console.log("Clerk invitation sign-up wiring checks passed.");
