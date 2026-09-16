import { apiErrorMessage, apiFetch, ApiError } from "@/lib/api";
import type { Document2Json } from "@drghaliasri/butex/document2";

export type ArticleStatus =
  | "draft"
  | "submitted"
  | "under_review"
  | "revision_requested"
  | "accepted"
  | "rejected"
  | "published";

export type ArticleSummary = {
  id: string;
  title: string;
  status: ArticleStatus;
  latest_version_number: number | null;
  updated_at: string;
  submitted_at: string | null;
};

export type VersionRead = {
  id: string;
  version_number: number;
  source_type: "zip_upload" | "web_editor";
  source_draft_revision_id: string | null;
  document_hash: string;
  title_snapshot: string;
  abstract_snapshot: string | null;
  submitted_at: string | null;
  created_at: string;
};

export type ArticleDetail = {
  id: string;
  title: string;
  abstract: string | null;
  status: ArticleStatus;
  current_draft_revision_id: string | null;
  draft_revision_number: number;
  created_at: string;
  updated_at: string;
  revision_request_note: string | null;
  revision_requested_for_version_id: string | null;
  revision_requested_at: string | null;
  revision_feedback: AuthorRevisionFeedback[];
  latest_version: VersionRead | null;
  versions: VersionRead[];
};

export type AuthorRevisionFeedback = {
  review_id: string;
  reviewer_label: string;
  comments_to_author: string;
  recommendation: "accept" | "minor_revision" | "major_revision" | "reject" | null;
};

export type DraftRevision = {
  revision_id: string;
  revision_number: number;
  document_hash: string;
  actor_type: "human" | "agent" | "system";
  reason:
    | "initial"
    | "autosave"
    | "ai_edit"
    | "metadata_edit"
    | "restore"
    | "revision_request";
  created_at: string;
  restored_from_id: string | null;
  restored_from_revision_number: number | null;
  document: Document2Json;
};

export type DraftRevisionHistoryItem = {
  revision_id: string;
  revision_number: number;
  document_hash: string;
  actor_type: "human" | "agent" | "system";
  reason: DraftRevision["reason"];
  created_at: string;
  created_by: string | null;
  created_by_name: string | null;
  restored_from_id: string | null;
  restored_from_revision_number: number | null;
  is_current: boolean;
};

export type DraftRevisionHistoryDetail = DraftRevisionHistoryItem & {
  document: Document2Json;
};

export type DraftCompileStatus = {
  status: "pending" | "processing" | "success" | "failed";
  compile_id: string | null;
  revision_id: string;
  revision_number: number;
  pdf_ready: boolean;
  error: { code: string; message: string } | null;
};

type GetToken = () => Promise<string | null>;
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

export function updateArticle(
  getToken: GetToken,
  id: string,
  input: { base_revision: number; title: string; abstract: string | null },
) {
  return apiFetch<ArticleDetail>(`/api/v1/articles/${id}`, getToken, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function getArticleDraft(getToken: GetToken, id: string) {
  return apiFetch<DraftRevision>(`/api/v1/articles/${id}/draft`, getToken);
}

export function putArticleDraft(
  getToken: GetToken,
  id: string,
  document: Document2Json,
  baseRevision: number,
) {
  return apiFetch<DraftRevision>(`/api/v1/articles/${id}/draft`, getToken, {
    method: "PUT",
    body: JSON.stringify({ document, base_revision: baseRevision }),
  });
}

export function listDraftRevisions(getToken: GetToken, id: string) {
  return apiFetch<DraftRevisionHistoryItem[]>(
    `/api/v1/articles/${id}/draft/revisions`,
    getToken,
  );
}

export function getDraftRevision(
  getToken: GetToken,
  id: string,
  revisionId: string,
) {
  return apiFetch<DraftRevisionHistoryDetail>(
    `/api/v1/articles/${id}/draft/revisions/${revisionId}`,
    getToken,
  );
}

export function restoreDraftRevision(
  getToken: GetToken,
  id: string,
  revisionId: string,
  baseRevision: number,
) {
  return apiFetch<DraftRevision>(
    `/api/v1/articles/${id}/draft/revisions/${revisionId}/restore`,
    getToken,
    {
      method: "POST",
      body: JSON.stringify({ base_revision: baseRevision }),
    },
  );
}

export function submitArticle(getToken: GetToken, id: string) {
  return apiFetch<ArticleDetail>(`/api/v1/articles/${id}/submit`, getToken, {
    method: "POST",
  });
}

export function deleteArticle(getToken: GetToken, id: string) {
  return apiFetch<void>(`/api/v1/articles/${id}`, getToken, { method: "DELETE" });
}

export type ArticleAssetUpload = { asset_id: string; content_type: string };
export type ArticleAssetSummary = {
  asset_id: string;
  content_type: string | null;
  size: number;
  updated_at: string | null;
};

export function listArticleAssets(getToken: GetToken, id: string) {
  return apiFetch<{ assets: ArticleAssetSummary[] }>(
    `/api/v1/articles/${id}/assets`,
    getToken,
  );
}

export function deleteArticleAsset(
  getToken: GetToken,
  id: string,
  assetKey: string,
) {
  const filename = assetKey.replace(/^assets\//, "");
  return apiFetch<void>(
    `/api/v1/articles/${id}/assets/${encodeURIComponent(filename)}`,
    getToken,
    { method: "DELETE" },
  );
}

export async function uploadArticleAsset(
  getToken: GetToken,
  id: string,
  file: File,
): Promise<ArticleAssetUpload> {
  const token = await getToken();
  const form = new FormData();
  form.append("file", file);
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}/api/v1/articles/${id}/assets`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!response.ok) {
    throw new ApiError(
      await apiErrorMessage(response, "تعذّر رفع الصورة."),
      response.status,
    );
  }
  return response.json() as Promise<ArticleAssetUpload>;
}

export async function fetchArticleAssetBlob(
  getToken: GetToken,
  id: string,
  assetKey: string,
): Promise<Blob> {
  const filename = assetKey.replace(/^assets\//, "");
  const token = await getToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(
    `${API_BASE}/api/v1/articles/${id}/assets/${encodeURIComponent(filename)}`,
    { headers },
  );
  if (!response.ok) throw new ApiError("تعذّر تحميل الصورة.", response.status);
  return response.blob();
}

export function requestDraftCompile(getToken: GetToken, id: string) {
  return apiFetch<DraftCompileStatus>(
    `/api/v1/articles/${id}/draft/compile`,
    getToken,
    { method: "POST" },
  );
}

export function getDraftCompileStatus(getToken: GetToken, id: string) {
  return apiFetch<DraftCompileStatus>(
    `/api/v1/articles/${id}/draft/compile/status`,
    getToken,
  );
}

function pdfFilenameFromResponse(response: Response): string {
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const utf8Match = disposition.match(/filename\*\s*=\s*UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1].trim());
    } catch {}
  }
  return disposition.match(/filename\s*=\s*"([^"]+)"/i)?.[1] || "compiled.pdf";
}

async function fetchPdf(getToken: GetToken, path: string): Promise<Blob> {
  const token = await getToken();
  const headers = new Headers({ "Cache-Control": "no-cache" });
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}?ts=${Date.now()}`, {
    cache: "no-store",
    headers,
  });
  if (!response.ok) throw new ApiError("تعذّر تحميل ملفّ المعاينة.", response.status);
  const blob = await response.blob();
  return new File([blob], pdfFilenameFromResponse(response), {
    type: blob.type || "application/pdf",
  });
}

export function fetchDraftPdfBlob(getToken: GetToken, id: string) {
  return fetchPdf(getToken, `/api/v1/articles/${id}/draft/pdf`);
}

export function fetchVersionPdfBlob(
  getToken: GetToken,
  articleId: string,
  versionId: string,
) {
  return fetchPdf(
    getToken,
    `/api/v1/articles/${articleId}/versions/${versionId}/pdf`,
  );
}

export function getVersionDocument(
  getToken: GetToken,
  articleId: string,
  versionId: string,
) {
  return apiFetch<{ document: Document2Json }>(
    `/api/v1/articles/${articleId}/versions/${versionId}/document`,
    getToken,
  );
}

export async function fetchVersionAssetBlob(
  getToken: GetToken,
  articleId: string,
  versionId: string,
  assetKey: string,
): Promise<Blob> {
  const filename = assetKey.replace(/^assets\//, "");
  const token = await getToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(
    `${API_BASE}/api/v1/articles/${articleId}/versions/${versionId}/assets/${encodeURIComponent(filename)}`,
    { headers },
  );
  if (!response.ok) throw new ApiError("تعذّر تحميل الصورة.", response.status);
  return response.blob();
}

export function fetchDraftCompileLog(getToken: GetToken, id: string) {
  return apiFetch<{ log: string }>(
    `/api/v1/articles/${id}/draft/compile/log`,
    getToken,
  );
}

export const STATUS_LABELS: Record<ArticleStatus, string> = {
  draft: "مسودة",
  submitted: "مُقدَّم",
  under_review: "قيد المراجعة",
  revision_requested: "مطلوب تعديل",
  accepted: "مقبول",
  rejected: "مرفوض",
  published: "منشور",
};
