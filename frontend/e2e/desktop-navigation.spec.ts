import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 1280, height: 800 } });

for (const menuName of ["للمؤلفين", "عن المجلة"]) {
  test(`${menuName} opens only by click and toggles closed`, async ({ page }) => {
    await page.goto("/");
    const trigger = page.getByRole("button", { name: menuName });
    const panelId = await trigger.getAttribute("aria-controls");
    expect(panelId).toBeTruthy();
    const menu = page.locator(`#${panelId}`);

    await trigger.hover();
    await expect(trigger).toHaveAttribute("aria-expanded", "false");
    await expect(menu).toBeHidden();

    await trigger.click();
    await expect(trigger).toHaveAttribute("aria-expanded", "true");
    await expect(menu).toBeVisible();

    await trigger.click();
    await expect(trigger).toHaveAttribute("aria-expanded", "false");
    await expect(menu).toBeHidden();
  });
}
