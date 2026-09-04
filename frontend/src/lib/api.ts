export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type UserGender = "male" | "female";

export type UserProfile = {
  id: string;
  clerk_id: string;
  email: string;
  full_name: string | null;
  gender: UserGender | null;
  affiliation: string | null;
  bio: string | null;
  created_at: string;
  updated_at: string;
};

export type UserProfileUpdate = {
  full_name?: string | null;
  affiliation?: string | null;
  bio?: string | null;
};

export type AccountDeletionRequestRead = {
  id: string;
  user_id: string;
  email_snapshot: string;
  reason: string | null;
  status: string;
  requested_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  resolution_note: string | null;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function containsArabic(value: string): boolean {
  return /[\u0600-\u06ff]/u.test(value);
}

export function arabicApiErrorMessage(
  data: unknown,
  fallback: string,
): string {
  if (!data || typeof data !== "object") return fallback;
  const detail = (data as {
    detail?: string | { msg?: string }[] | { message?: string };
  }).detail;
  const candidate =
    typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail[0]?.msg
        : detail?.message;
  return typeof candidate === "string" && containsArabic(candidate)
    ? candidate
    : fallback;
}

export async function apiErrorMessage(
  response: Response,
  fallback = "حدث خطأ أثناء الاتصال بالخادم.",
): Promise<string> {
  try {
    const message = arabicApiErrorMessage(await response.json(), "");
    if (message) return message;
  } catch {
    // Use the localized status or operation fallback below.
  }
  if (response.status === 401) return "انتهت الجلسة، سجّل دخولك مجدداً.";
  if (response.status === 503) return "الخدمة غير متاحة مؤقتاً.";
  return fallback;
}

export async function apiFetch<T>(
  path: string,
  getToken: () => Promise<string | null>,
  options: RequestInit = {},
): Promise<T> {
  const token = await getToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new ApiError(await apiErrorMessage(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function getCurrentUser(getToken: () => Promise<string | null>) {
  return apiFetch<UserProfile>("/api/v1/users/me", getToken);
}

export function updateCurrentUser(
  getToken: () => Promise<string | null>,
  payload: UserProfileUpdate,
) {
  return apiFetch<UserProfile>("/api/v1/users/me", getToken, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
