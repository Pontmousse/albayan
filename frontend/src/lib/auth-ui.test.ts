import { describe, expect, it } from "vitest";
import { translateEnglishAuthMessage } from "./auth-ui";

describe("translateEnglishAuthMessage", () => {
  it("translates known Clerk messages", () => {
    expect(translateEnglishAuthMessage("You're already signed in.")).toBe(
      "أنت مسجّل الدخول بالفعل.",
    );
  });

  it("does not expose unknown English Clerk messages", () => {
    expect(translateEnglishAuthMessage("A new upstream error")).toBe(
      "تعذّر إكمال عملية المصادقة. حاول مجدداً.",
    );
  });

  it("keeps Arabic authentication messages", () => {
    expect(translateEnglishAuthMessage("انتهت الجلسة.")).toBe("انتهت الجلسة.");
  });
});
