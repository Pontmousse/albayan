import { describe, expect, it } from "vitest";
import { ApiError, apiErrorMessage, arabicApiErrorMessage } from "./api";
import { userFacingErrorMessage } from "./user-facing-errors";

describe("arabicApiErrorMessage", () => {
  it("keeps Arabic API details", () => {
    expect(
      arabicApiErrorMessage({ detail: "المقال غير موجود." }, "خطأ عام"),
    ).toBe("المقال غير موجود.");
  });

  it("does not expose non-Arabic service details", () => {
    expect(
      arabicApiErrorMessage({ detail: "compiler connection failed" }, "خطأ عام"),
    ).toBe("خطأ عام");
  });

  it("does not expose mixed Arabic and internal details", () => {
    const fallback = "تعذّر إنشاء ملفّ المعاينة.";
    const unsafeDetails = [
      "تعذّر التحقق: Document2 validation failed.",
      "تعذّر الاتصال. راجع NEXT_PUBLIC_API_URL.",
      "تعذّر الطلب إلى /api/v1/articles/123/compile.",
      "خدمة التجميع غير مُهيّأة على الخادم.",
      "تعذّر التنفيذ.\n    at compilePreview (page.tsx:42:3)",
    ];

    for (const detail of unsafeDetails) {
      expect(arabicApiErrorMessage({ detail }, fallback)).toBe(fallback);
    }
  });

  it("keeps safe Arabic validation guidance", () => {
    expect(
      arabicApiErrorMessage(
        { detail: "احفظ المخطوطة ثم أعد إنشاء ملفّ المعاينة." },
        "تعذّر إنشاء ملفّ المعاينة.",
      ),
    ).toBe("احفظ المخطوطة ثم أعد إنشاء ملفّ المعاينة.");
  });

  it("keeps only safe ApiError messages at the UI boundary", () => {
    expect(
      userFacingErrorMessage(
        new ApiError("المقال غير موجود.", 404),
        "تعذّر تحميل المقال.",
      ),
    ).toBe("المقال غير موجود.");
    expect(
      userFacingErrorMessage(
        new ApiError("تعذّر الاتصال بعامل BuTeX.", 502),
        "تعذّر تحميل المقال.",
      ),
    ).toBe("تعذّر تحميل المقال.");
    expect(
      userFacingErrorMessage(
        new ApiError("حدث خطأ أثناء الاتصال بالخادم.", 500),
        "تعذّر تحميل المقال.",
      ),
    ).toBe("تعذّر تحميل المقال.");
  });
});

describe("apiErrorMessage", () => {
  it("uses the Arabic session message for unauthorized responses", async () => {
    const response = new Response(JSON.stringify({ detail: "Unauthorized" }), {
      status: 401,
    });

    await expect(apiErrorMessage(response)).resolves.toBe(
      "انتهت الجلسة، سجّل دخولك مجدداً.",
    );
  });
});
