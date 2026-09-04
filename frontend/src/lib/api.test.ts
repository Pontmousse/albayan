import { describe, expect, it } from "vitest";
import { apiErrorMessage, arabicApiErrorMessage } from "./api";

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
