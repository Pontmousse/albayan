import { describe, expect, it } from "vitest";
import {
  isSafeArabicProductMessage,
  UserFacingError,
  userFacingErrorMessage,
} from "./user-facing-errors";

describe("isSafeArabicProductMessage", () => {
  it("accepts concise Arabic product copy", () => {
    expect(isSafeArabicProductMessage("تعذّر حفظ التغييرات.")).toBe(true);
    expect(
      isSafeArabicProductMessage("نوع الملف غير مدعوم. استخدم JPEG أو PNG."),
    ).toBe(true);
  });

  it.each([
    "Document2 validation failed; المخطوطة غير صالحة.",
    "تعذّر الاتصال بعامل BuTeX.",
    "تعذّر الاتصال. راجع COMPILER_URL.",
    "تعذّر الطلب إلى /api/v1/articles/123.",
    "تعذّر التنفيذ.\n    at render (page.tsx:10:2)",
    "خدمة التجميع غير مُهيّأة على الخادم.",
    "تعذّر الاتصال بخدمة التجميع.",
  ])("rejects technical detail: %s", (message) => {
    expect(isSafeArabicProductMessage(message)).toBe(false);
  });
});

describe("userFacingErrorMessage", () => {
  const fallback = "تعذّر إنشاء ملفّ المعاينة.";

  it("keeps an explicitly trusted product error", () => {
    expect(
      userFacingErrorMessage(
        new UserFacingError("راجع المخطوطة ثم حاول مجدداً."),
        fallback,
      ),
    ).toBe("راجع المخطوطة ثم حاول مجدداً.");
  });

  it("does not trust an arbitrary Error even when its message is Arabic", () => {
    expect(
      userFacingErrorMessage(
        new Error("تعذّر التحقق: Document2 validation failed."),
        fallback,
      ),
    ).toBe(fallback);
  });

  it("rejects technical detail accidentally wrapped as a product error", () => {
    expect(
      userFacingErrorMessage(
        new UserFacingError("تعذّر الاتصال. راجع NEXT_PUBLIC_API_URL."),
        fallback,
      ),
    ).toBe(fallback);
  });

  it("prefers the operation fallback over a generic connection error", () => {
    expect(
      userFacingErrorMessage(
        new UserFacingError("حدث خطأ أثناء الاتصال بالخادم."),
        fallback,
      ),
    ).toBe(fallback);
  });
});
