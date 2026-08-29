import { apiFetch } from "@/lib/api";

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

type GetToken = () => Promise<string | null>;

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
