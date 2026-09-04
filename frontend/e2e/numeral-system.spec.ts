import { expect, test } from "@playwright/test";

test("switches numeral systems and persists across navigation and reload", async ({
  page,
}) => {
  await page.goto("/al-durus");
  await page.evaluate(() => localStorage.removeItem("albayan:numeral-system"));
  await page.reload();
  await page.waitForFunction(
    () => document.documentElement.dataset.numeralReady === "true",
  );

  await expect(page.getByText("١ من ٢", { exact: true })).toBeVisible();
  const toggle = page.getByRole("button", { name: "استخدام الأرقام الغربية" });
  await toggle.click();
  await expect(page.getByText("1 من 2", { exact: true })).toBeVisible();

  await page
    .getByRole("main")
    .getByRole("link", { name: "إرشادات المؤلفين" })
    .click();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "استخدام الأرقام العربية المشرقية" }),
  ).toBeVisible();

  await page.goto("/al-durus");
  await expect(page.getByText("1 من 2", { exact: true })).toBeVisible();
});

test("formats the Quranic verse reference with the selected numeral system", async ({
  page,
}) => {
  await page.goto("/");
  await page.evaluate(() => localStorage.removeItem("albayan:numeral-system"));
  await page.reload();
  await page.waitForFunction(
    () => document.documentElement.dataset.numeralReady === "true",
  );

  await expect(page.getByText("سورة فاطر [٢٧، ٢٨، ٢٩، ٣٠]", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "استخدام الأرقام الغربية" }).click();
  await expect(page.getByText("سورة فاطر [27، 28، 29، 30]", { exact: true })).toBeVisible();
});
