import { apiFetch, ApiError } from "@/lib/api";
import type { VersionRead, VersionStatus } from "@/lib/api/articles";
import type { ReviewRecommendation } from "@/lib/api/reviews";

export type EditorArticleSummary = {
  id: string;
  title: string;
  status: VersionStatus;
  version_number: number;
  updated_at: string;
  submitted_at: string | null;
  submitted_reviews_count: number;
};

export type EditorReviewReport = {
  id: string;
  reviewer_name: string | null;
  reviewer_email: string;
  comments_to_author: string | null;
  comments_to_editor: string | null;
  recommendation: ReviewRecommendation | null;
  submitted_at: string | null;
};

export type EditorArticleDetail = {
  id: string;
  title: string;
  abstract: string | null;
  created_at: string;
  updated_at: string;
  current_version: VersionRead;
  versions: VersionRead[];
  reviews: EditorReviewReport[];
};

export type EditorDecisionStatus = "under_review" | "accepted" | "rejected";

type GetToken = () => Promise<string | null>;

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function listEditorArticles(getToken: GetToken) {
  return apiFetch<EditorArticleSummary[]>("/api/v1/editor/articles", getToken);
}

export function getEditorArticle(getToken: GetToken, articleId: string) {
  return apiFetch<EditorArticleDetail>(
    `/api/v1/editor/articles/${articleId}`,
    getToken,
  );
}

export function getEditorDocument(getToken: GetToken, articleId: string) {
  return apiFetch<{ document: unknown | null }>(
    `/api/v1/editor/articles/${articleId}/document`,
    getToken,
  );
}

export function postEditorDecision(
  getToken: GetToken,
  articleId: string,
  status: EditorDecisionStatus,
  reason?: string | null,
) {
  return apiFetch<VersionRead>(
    `/api/v1/editor/articles/${articleId}/decision`,
    getToken,
    {
      method: "POST",
      body: JSON.stringify({ status, reason: reason ?? null }),
    },
  );
}

export async function fetchEditorAssetBlob(
  getToken: GetToken,
  articleId: string,
  assetKey: string,
): Promise<Blob> {
  const filename = assetKey.replace(/^assets\//, "");
  const token = await getToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(
    `${API_BASE}/api/v1/editor/articles/${articleId}/assets/${encodeURIComponent(filename)}`,
    { headers },
  );
  if (!response.ok) {
    throw new ApiError("تعذّر تحميل الصورة.", response.status);
  }
  return response.blob();
}
