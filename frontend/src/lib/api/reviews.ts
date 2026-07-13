import { apiFetch, ApiError } from "@/lib/api";
import type { VersionStatus } from "@/lib/api/articles";

export type ReviewRecommendation =
  | "accept"
  | "minor_revision"
  | "major_revision"
  | "reject";

export type ReviewStatus = "draft" | "submitted";

export type ReviewerAssignmentStatus =
  | "invited"
  | "accepted"
  | "declined"
  | "completed";

export type ReviewRead = {
  id: string;
  comments_to_author: string | null;
  comments_to_editor: string | null;
  recommendation: ReviewRecommendation | null;
  status: ReviewStatus;
  submitted_at: string | null;
  article_version_id: string;
};

export type AssignmentSummary = {
  id: string;
  article_id: string;
  article_title: string;
  assignment_status: ReviewerAssignmentStatus;
  version_status: VersionStatus;
  version_number: number;
  review: ReviewRead | null;
  invited_at: string;
};

export type AssignmentDetail = {
  id: string;
  article_id: string;
  article_title: string;
  article_abstract: string | null;
  assignment_status: ReviewerAssignmentStatus;
  version_status: VersionStatus;
  version_number: number;
  version_id: string;
  compile_status: "pending" | "processing" | "success" | "failed";
  review: ReviewRead | null;
  invited_at: string;
  accepted_at: string | null;
};

export type ReviewWrite = {
  comments_to_author?: string | null;
  comments_to_editor?: string | null;
  recommendation?: ReviewRecommendation | null;
};

type GetToken = () => Promise<string | null>;

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function listMyAssignments(getToken: GetToken) {
  return apiFetch<AssignmentSummary[]>("/api/v1/reviews/me", getToken);
}

export function getAssignment(getToken: GetToken, assignmentId: string) {
  return apiFetch<AssignmentDetail>(
    `/api/v1/reviews/assignments/${assignmentId}`,
    getToken,
  );
}

export function getAssignmentDocument(getToken: GetToken, assignmentId: string) {
  return apiFetch<{ document: unknown | null }>(
    `/api/v1/reviews/assignments/${assignmentId}/document`,
    getToken,
  );
}

export function saveReviewDraft(
  getToken: GetToken,
  assignmentId: string,
  payload: ReviewWrite,
) {
  return apiFetch<ReviewRead>(
    `/api/v1/reviews/assignments/${assignmentId}/review`,
    getToken,
    { method: "PUT", body: JSON.stringify(payload) },
  );
}

export function submitReview(getToken: GetToken, assignmentId: string) {
  return apiFetch<ReviewRead>(
    `/api/v1/reviews/assignments/${assignmentId}/review/submit`,
    getToken,
    { method: "POST" },
  );
}

export async function fetchAssignmentAssetBlob(
  getToken: GetToken,
  assignmentId: string,
  assetKey: string,
): Promise<Blob> {
  const filename = assetKey.replace(/^assets\//, "");
  const token = await getToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(
    `${API_BASE}/api/v1/reviews/assignments/${assignmentId}/assets/${encodeURIComponent(filename)}`,
    { headers },
  );
  if (!response.ok) {
    throw new ApiError("تعذّر تحميل الصورة.", response.status);
  }
  return response.blob();
}

export async function fetchAssignmentPdfBlob(
  getToken: GetToken,
  assignmentId: string,
): Promise<Blob> {
  const token = await getToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(
    `${API_BASE}/api/v1/reviews/assignments/${assignmentId}/pdf`,
    { headers },
  );
  if (!response.ok) {
    throw new ApiError("تعذّر تحميل ملف PDF.", response.status);
  }
  return response.blob();
}

export const RECOMMENDATION_LABELS: Record<ReviewRecommendation, string> = {
  accept: "قبول",
  minor_revision: "تعديلات طفيفة",
  major_revision: "تعديلات جوهرية",
  reject: "رفض",
};
