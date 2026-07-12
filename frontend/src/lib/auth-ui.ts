const CLERK_ERROR_MAP: Record<string, string> = {
  form_password_incorrect: "كلمة المرور غير صحيحة.",
  form_password_or_identifier_incorrect: "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
  form_identifier_not_found: "البريد الإلكتروني غير مسجّل.",
  form_password_pwned: "كلمة المرور ضعيفة أو مستخدمة في اختراق سابق. اختر كلمة مرور أخرى.",
  form_password_compromised: "كلمة المرور معرّضة للاختراق. استخدم طريقة دخول بديلة ثم غيّر كلمة المرور.",
  form_password_length_too_short: "كلمة المرور قصيرة جداً.",
  form_password_length_too_long: "كلمة المرور طويلة جداً.",
  form_password_no_lowercase: "يجب أن تحتوي كلمة المرور على حرف صغير واحد على الأقل (a-z).",
  form_password_no_uppercase: "يجب أن تحتوي كلمة المرور على حرف كبير واحد على الأقل (A-Z).",
  form_password_no_number: "يجب أن تحتوي كلمة المرور على رقم واحد على الأقل.",
  form_password_no_special_char: "يجب أن تحتوي كلمة المرور على رمز خاص واحد على الأقل.",
  form_password_not_strong_enough: "كلمة المرور ضعيفة. اختر كلمة أقوى.",
  form_password_validation_failed: "كلمة المرور لا تستوفي متطلبات الأمان.",
  form_password_size_in_bytes_exceeded: "كلمة المرور طويلة جداً. استخدم كلمة أقصر.",
  form_param_format_invalid: "صيغة البريد الإلكتروني غير صحيحة.",
  form_param_nil: "يرجى ملء جميع الحقول المطلوبة.",
  form_identifier_exists: "هذا البريد الإلكتروني مسجّل مسبقاً. جرّب تسجيل الدخول.",
  form_code_incorrect: "رمز التحقق غير صحيح.",
  form_password_digest_invalid_code: "رمز إعادة تعيين كلمة المرور غير صالح.",
  not_allowed_access: "الوصول غير مسموح.",
  not_allowed_to_sign_up: "التسجيل غير مسموح حالياً.",
  session_exists: "أنت مسجّل الدخول بالفعل.",
  user_locked: "الحساب مقفل مؤقتاً. حاول لاحقاً.",
  captcha_invalid: "فشل التحقق الأمني. أعد المحاولة.",
};

const ENGLISH_MESSAGE_PATTERNS: { pattern: RegExp; replace: string | ((match: RegExpMatchArray) => string) }[] = [
  {
    pattern: /passwords? must (?:be )?at least (\d+) characters?/i,
    replace: (m) => `يجب أن تكون كلمة المرور ${m[1]} أحرف على الأقل.`,
  },
  {
    pattern: /enter a password with at least (\d+) characters?/i,
    replace: (m) => `أدخل كلمة مرور من ${m[1]} أحرف على الأقل.`,
  },
  {
    pattern: /passwords? must contain at least one lowercase character/i,
    replace: "يجب أن تحتوي كلمة المرور على حرف صغير واحد على الأقل (a-z).",
  },
  {
    pattern: /passwords? must contain at least one uppercase character/i,
    replace: "يجب أن تحتوي كلمة المرور على حرف كبير واحد على الأقل (A-Z).",
  },
  {
    pattern: /passwords? must contain at least one number/i,
    replace: "يجب أن تحتوي كلمة المرور على رقم واحد على الأقل.",
  },
  {
    pattern: /passwords? must contain at least one special character/i,
    replace: "يجب أن تحتوي كلمة المرور على رمز خاص واحد على الأقل.",
  },
  {
    pattern: /given password is not strong enough/i,
    replace: "كلمة المرور ضعيفة. اختر كلمة أقوى.",
  },
  {
    pattern: /your password is too long/i,
    replace: "كلمة المرور طويلة جداً. استخدم كلمة أقصر.",
  },
  {
    pattern: /password has been found in an online data breach/i,
    replace: "كلمة المرور مستخدمة في اختراق معروف. اختر كلمة مرور أخرى.",
  },
  {
    pattern: /is invalid/i,
    replace: "القيمة المدخلة غير صالحة.",
  },
  {
    pattern: /couldn't find your account/i,
    replace: "لم يُعثر على حساب بهذا البريد.",
  },
  {
    pattern: /incorrect password/i,
    replace: "كلمة المرور غير صحيحة.",
  },
];

type ClerkLikeError = {
  code?: string;
  longMessage?: string;
  message?: string;
  meta?: Record<string, unknown>;
};

function translateClerkErrorObject(error: ClerkLikeError): string | null {
  if (error.code) {
    if (error.code === "form_password_length_too_short") {
      const minLength = error.meta?.min_length ?? error.meta?.minLength;
      if (typeof minLength === "number") {
        return `يجب أن تكون كلمة المرور ${minLength} أحرف على الأقل.`;
      }
    }
    if (CLERK_ERROR_MAP[error.code]) {
      return CLERK_ERROR_MAP[error.code];
    }
  }

  if (error.longMessage) {
    return translateEnglishAuthMessage(error.longMessage);
  }
  if (error.message) {
    return translateEnglishAuthMessage(error.message);
  }

  return null;
}

export function translateEnglishAuthMessage(message: string): string {
  const trimmed = message.trim();
  for (const { pattern, replace } of ENGLISH_MESSAGE_PATTERNS) {
    const match = trimmed.match(pattern);
    if (match) {
      return typeof replace === "function" ? replace(match) : replace;
    }
  }
  return trimmed;
}

export function translateClerkError(error: unknown): string {
  if (
    error &&
    typeof error === "object" &&
    "code" in error &&
    typeof (error as { code: unknown }).code === "string"
  ) {
    const translated = translateClerkErrorObject(error as ClerkLikeError);
    if (translated) return translated;
  }

  if (
    error &&
    typeof error === "object" &&
    "errors" in error &&
    Array.isArray((error as { errors: unknown[] }).errors)
  ) {
    const errors = (error as { errors: ClerkLikeError[] }).errors;
    const messages = errors
      .map((item) => translateClerkErrorObject(item))
      .filter((msg): msg is string => Boolean(msg));
    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  if (error instanceof Error && error.message) {
    return translateEnglishAuthMessage(error.message);
  }

  return "حدث خطأ غير متوقع. حاول مجدداً.";
}

export function setArabicFieldValidity(input: HTMLInputElement) {
  if (input.validity.valueMissing) {
    input.setCustomValidity("يرجى ملء هذا الحقل.");
    return;
  }

  if (input.validity.typeMismatch && input.type === "email") {
    input.setCustomValidity("صيغة البريد الإلكتروني غير صحيحة.");
    return;
  }

  if (input.validity.tooShort && input.minLength > 0) {
    input.setCustomValidity(`يجب إدخال ${input.minLength} أحرف على الأقل.`);
    return;
  }

  input.setCustomValidity("");
}

export const inputClassName =
  "w-full rounded-md border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-1 focus:ring-[var(--journal-accent)]";

export const passwordInputClassName =
  "w-full rounded-md border border-[var(--journal-border)] bg-white py-2 ps-3 pe-10 text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:ring-1 focus:ring-[var(--journal-accent)]";

export const buttonClassName =
  "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-md bg-[var(--journal-accent)] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-60";

export const cardClassName =
  "rounded-xl border border-[var(--journal-border)] bg-white/80 p-4 shadow-sm sm:p-6";

export const PASSWORD_MIN_LENGTH_HINT =
  "يجب أن تكون كلمة المرور 8 أحرف على الأقل، وتتضمن أحرفاً كبيرة وصغيرة وأرقاماً ورموزاً حسب إعدادات الأمان.";
