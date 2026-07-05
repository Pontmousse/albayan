import { apiFetch } from "@/lib/api";

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

export const STATUS_LABELS: Record<VersionStatus, string> = {
  draft: "مسودة",
  submitted: "مُقدَّم",
  under_review: "قيد المراجعة",
  accepted: "مقبول",
  rejected: "مرفوض",
  published: "منشور",
};
