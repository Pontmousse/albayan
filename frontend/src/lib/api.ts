const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type UserProfile = {
  id: string;
  clerk_id: string;
  email: string;
  full_name: string | null;
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

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string | { msg?: string }[] };
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      return data.detail[0].msg;
    }
  } catch {
    // ignore
  }
  if (response.status === 401) return "انتهت الجلسة، سجّل دخولك مجدداً.";
  if (response.status === 503) return "الخدمة غير متاحة مؤقتاً.";
  return "حدث خطأ أثناء الاتصال بالخادم.";
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
    throw new ApiError(await parseError(response), response.status);
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
