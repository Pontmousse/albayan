import { ApiError, apiErrorMessage, apiFetch } from "@/lib/api";

export type IssueStatus = "open" | "in_progress" | "resolved" | "closed";
export type IssueCategory = "bug" | "feature_request" | "feedback";

export type IssueReporter = {
  id: string;
  full_name: string | null;
};

export type IssueImage = {
  id: string;
  s3_key: string;
  position: number;
};

export type IssueRead = {
  id: string;
  user_id: string;
  title: string;
  description: string;
  status: IssueStatus;
  category: IssueCategory;
  upvote_count: number;
  current_user_upvoted: boolean;
  reporter: IssueReporter;
  images: IssueImage[];
  created_at: string;
  updated_at: string;
};

export type IssueCreateInput = {
  title: string;
  description: string;
  category: IssueCategory;
};

export const ISSUE_STATUS_LABELS: Record<IssueStatus, string> = {
  open: "مفتوح",
  in_progress: "قيد المعالجة",
  resolved: "تم الحل",
  closed: "مغلق",
};

export const ISSUE_CATEGORY_LABELS: Record<IssueCategory, string> = {
  bug: "خلل",
  feature_request: "طلب ميزة",
  feedback: "ملاحظة",
};

type GetToken = (options?: { skipCache?: boolean }) => Promise<string | null>;
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type IssueListParams = {
  status?: IssueStatus | null;
  category?: IssueCategory | null;
  sort?: "date" | "upvotes";
  direction?: "asc" | "desc";
};

export function listIssues(getToken: GetToken, params: IssueListParams = {}) {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.category) search.set("category", params.category);
  if (params.sort) search.set("sort", params.sort);
  if (params.direction) search.set("direction", params.direction);
  const qs = search.toString();
  return apiFetch<IssueRead[]>(`/api/v1/issues${qs ? `?${qs}` : ""}`, getToken);
}

export function createIssue(getToken: GetToken, input: IssueCreateInput) {
  return apiFetch<IssueRead>("/api/v1/issues", getToken, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function createIssueWithImages(
  getToken: GetToken,
  input: IssueCreateInput,
  files: readonly File[],
): Promise<IssueRead> {
  const token = await getToken({ skipCache: true });
  const form = new FormData();
  form.append("title", input.title);
  form.append("description", input.description);
  form.append("category", input.category);
  files.forEach((file) => form.append("files", file));

  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}/api/v1/issues/with-images`, {
    method: "POST",
    headers,
    body: form,
  });

  if (!response.ok) {
    throw new ApiError(
      await apiErrorMessage(response, "تعذّر إرسال البلاغ."),
      response.status,
    );
  }

  return response.json() as Promise<IssueRead>;
}

export function getIssue(getToken: GetToken, id: string) {
  return apiFetch<IssueRead>(`/api/v1/issues/${id}`, getToken);
}

export function upvoteIssue(getToken: GetToken, id: string) {
  return apiFetch<IssueRead>(`/api/v1/issues/${id}/upvote`, getToken, {
    method: "POST",
  });
}

export function removeIssueUpvote(getToken: GetToken, id: string) {
  return apiFetch<IssueRead>(`/api/v1/issues/${id}/upvote`, getToken, {
    method: "DELETE",
  });
}

export async function uploadIssueImage(
  getToken: GetToken,
  issueId: string,
  file: File,
): Promise<IssueRead> {
  const token = await getToken();
  const form = new FormData();
  form.append("file", file);

  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(
    `${API_BASE}/api/v1/issues/${issueId}/images`,
    {
      method: "POST",
      headers,
      body: form,
    },
  );

  if (!response.ok) {
    throw new ApiError(
      await apiErrorMessage(response, "تعذّر رفع الصورة."),
      response.status,
    );
  }

  return response.json() as Promise<IssueRead>;
}

export async function fetchIssueImageBlob(
  getToken: GetToken,
  issueId: string,
  imageId: string,
): Promise<Blob> {
  const token = await getToken();
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(
    `${API_BASE}/api/v1/issues/${issueId}/images/${imageId}`,
    { headers },
  );

  if (!response.ok) {
    throw new ApiError("تعذّر تحميل الصورة.", response.status);
  }

  return response.blob();
}

export function deleteIssueImage(
  getToken: GetToken,
  issueId: string,
  imageId: string,
) {
  return apiFetch<IssueRead>(
    `/api/v1/issues/${issueId}/images/${imageId}`,
    getToken,
    { method: "DELETE" },
  );
}
