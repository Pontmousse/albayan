import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const frontendRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const srcRoot = join(frontendRoot, "src");
const uiRoots = [join(srcRoot, "app"), join(srcRoot, "components")];
const rawMessageAllowlist = new Set([
  "components/dashboard/exported-tex-dev-panel.tsx",
]);

function readSrc(path) {
  return readFileSync(join(srcRoot, path), "utf8");
}

function listTsxFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return listTsxFiles(path);
    return entry.isFile() && entry.name.endsWith(".tsx") ? [path] : [];
  });
}

test("normal UI files do not read arbitrary exception messages", () => {
  for (const root of uiRoots) {
    for (const path of listTsxFiles(root)) {
      const rel = relative(srcRoot, path);
      if (rawMessageAllowlist.has(rel)) continue;
      const source = readFileSync(path, "utf8");
      assert.equal(
        source.includes(".message"),
        false,
        `${rel} must map failures to Arabic product copy`,
      );
    }
  }
});

test("article preview never appends the export exception", () => {
  const article = readSrc("app/maktabi/(lawha)/maqalati/[id]/page.tsx");
  const viewer = readSrc("components/dashboard/compiled-pdf-viewer.tsx");

  assert.match(article, /throw new UserFacingError\([\s\S]*تعذّر إنشاء ملفّ المعاينة/);
  assert.equal(article.includes("تعذّر تصدير المخطوطة:"), false);
  assert.equal(article.includes("${err.message}"), false);
  assert.match(viewer, /userFacingErrorMessage/);
  assert.match(viewer, /تعذّر تحميل ملفّ المعاينة\. حاول مجدداً\./);
  assert.match(
    viewer,
    /تعذّر إنشاء ملفّ المعاينة\. راجع المخطوطة ثم حاول مجدداً\./,
  );
  assert.equal(viewer.includes(".message"), false);
});

test("OAuth error copy does not expose request parameter names", () => {
  const source = readSrc("components/oauth/oauth-consent-form.tsx");
  assert.equal(source.includes("تنقص معاملات OAuth المطلوبة"), false);
  assert.match(source, /تعذّر إكمال طلب التفويض/);
});

test("repository guidance permanently documents the UI error boundary", () => {
  const agents = readFileSync(join(frontendRoot, "..", "AGENTS.md"), "utf8");
  assert.match(agents, /## رسائل الأخطاء للمستخدم/);
  assert.match(agents, /لا تعرض `err\.message`/);
  assert.match(agents, /أدوات التطوير/);
});
