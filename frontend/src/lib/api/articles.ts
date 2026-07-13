import { apiFetch, ApiError } from "@/lib/api";

export type VersionStatus =
  | "draft"
  | "submitted"
  | "under_review"
  | "accepted"
  | "rejected"
  | "published";

export type ArticleSummary = {
  id: string;
  title: string;
  status: VersionStatus;
  version_number: number;
  updated_at: string;
  submitted_at: string | null;
};

export type VersionRead = {
  id: string;
  version_number: number;
  status: VersionStatus;
  source_type: "zip_upload" | "web_editor";
  compile_status: "pending" | "processing" | "success" | "failed";
  change_summary: string | null;
  submitted_at: string | null;
  created_at: string;
};

export type ArticleDetail = {
  id: string;
  title: string;
  abstract: string | null;
  created_at: string;
  updated_at: string;
  current_version: VersionRead;
  versions: VersionRead[];
};

type GetToken = () => Promise<string | null>;

export function listMyArticles(getToken: GetToken) {
  return apiFetch<ArticleSummary[]>("/api/v1/articles/me", getToken);
}

export function createArticle(
  getToken: GetToken,
  input: { title: string; abstract?: string | null },
) {
  return apiFetch<ArticleDetail>("/api/v1/articles", getToken, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getArticle(getToken: GetToken, id: string) {
  return apiFetch<ArticleDetail>(`/api/v1/articles/${id}`, getToken);
}

export function getArticleDocument(getToken: GetToken, id: string) {
  return apiFetch<{ document: unknown | null }>(
    `/api/v1/articles/${id}/document`,
    getToken,
  );
}

export function saveArticleDocument(
  getToken: GetToken,
  id: string,
  document: unknown,
) {
  return apiFetch<{ ok: boolean }>(`/api/v1/articles/${id}/document`, getToken, {
    method: "PUT",
    body: JSON.stringify({ document }),
  });
}

export function submitArticle(getToken: GetToken, id: string) {
  return apiFetch<VersionRead>(`/api/v1/articles/${id}/submit`, getToken, {
    method: "POST",
  });
}

export type ArticleAssetUpload = {
  asset_id: string;
  content_type: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function uploadArticleAsset(
  getToken: GetToken,
  id: string,
  file: File,
): Promise<ArticleAssetUpload> {
  const token = await getToken();
  const form = new FormData();
  form.append("file", file);

  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}/api/v1/articles/${id}/assets`, {
    method: "POST",
    headers,
    body: form,
  });

  if (!response.ok) {
    let message = "تعذّر رفع الصورة.";
    try {
      const data = (await response.json()) as { detail?: string };
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      // ignore
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<ArticleAssetUpload>;
}

/** يجلب بايتات أصل صورة — assetKey مثل assets/uuid.jpg */
export async function fetchArticleAssetBlob(
  getToken: GetToken,
  id: string,
  assetKey: string,
): Promise<Blob> {
  const filename = assetKey.replace(/^assets\//, "");
  const token = await getToken();
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(
    `${API_BASE}/api/v1/articles/${id}/assets/${encodeURIComponent(filename)}`,
    { headers },
  );

  if (!response.ok) {
    throw new ApiError("تعذّر تحميل الصورة.", response.status);
  }

  return response.blob();
}

export function requestArticleCompile(getToken: GetToken, id: string) {
  return apiFetch<VersionRead>(`/api/v1/articles/${id}/compile`, getToken, {
    method: "POST",
  });
}

/** يجلب compiled.pdf للإصدار الحالي */
export async function fetchArticlePdfBlob(
  getToken: GetToken,
  id: string,
): Promise<Blob> {
  const token = await getToken();
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}/api/v1/articles/${id}/pdf`, {
    headers,
  });

  if (!response.ok) {
    throw new ApiError("تعذّر تحميل ملف PDF.", response.status);
  }

  return response.blob();
}

export const STATUS_LABELS: Record<VersionStatus, string> = {
  draft: "مسودة",
  submitted: "مُقدَّم",
  under_review: "قيد المراجعة",
  accepted: "مقبول",
  rejected: "مرفوض",
  published: "منشور",
};
