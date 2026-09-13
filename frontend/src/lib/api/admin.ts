import { apiFetch, type UserGender } from "@/lib/api";
import type { VersionRead, VersionStatus } from "@/lib/api/articles";
import type {
  IssueCategory,
  IssueImage,
  IssueStatus,
} from "@/lib/api/issues";
import { buildMcpCallsPath } from "@/lib/api/admin-mcp-query";

export type ReviewerAssignmentStatus =
  | "invited"
  | "accepted"
  | "declined"
  | "completed";

export type InvitationRole = "reviewer" | "editor";

export type InvitationStatus =
  | "pending"
  | "accepted"
  | "expired"
  | "cancelled";

export type AdminUserBrief = {
  id: string;
  email: string;
  full_name: string | null;
  gender: UserGender | null;
};

export type AdminAuthorRead = {
  user: AdminUserBrief;
  author_order: number;
  is_corresponding: boolean;
};

export type AdminReviewerRead = {
  user: AdminUserBrief;
  status: ReviewerAssignmentStatus;
  invited_at: string;
  review_due_at: string | null;
  accepted_at: string | null;
  declined_at: string | null;
};

export type AdminEditorRead = {
  user: AdminUserBrief;
  assigned_at: string;
  assigned_by: string | null;
};

export type AdminArticleSummary = {
  id: string;
  title: string;
  status: VersionStatus;
  version_number: number;
  updated_at: string;
  submitted_at: string | null;
  authors: AdminAuthorRead[];
  reviewers: AdminReviewerRead[];
  editors: AdminEditorRead[];
};

export type AdminArticleDetail = {
  id: string;
  title: string;
  abstract: string | null;
  created_at: string;
  updated_at: string;
  current_version: VersionRead;
  versions: VersionRead[];
  authors: AdminAuthorRead[];
  reviewers: AdminReviewerRead[];
  editors: AdminEditorRead[];
};

export type AdminUserListItem = {
  id: string;
  clerk_id: string;
  email: string;
  full_name: string | null;
  gender: UserGender | null;
  roles: string[];
  created_at: string;
};

export type AppInvitationStatus =
  | "pending"
  | "accepted"
  | "revoked"
  | "expired"
  | string;

export type AppInvitationRead = {
  id: string;
  email: string;
  full_name: string | null;
  gender: UserGender | null;
  status: AppInvitationStatus;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
};

export type AppInvitationCreateResponse = {
  invitation: AppInvitationRead;
};

export type AccountDeletionRequestStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "completed";

export type AccountDeletionRequestAdminRead = {
  id: string;
  user_id: string;
  email_snapshot: string;
  reason: string | null;
  status: AccountDeletionRequestStatus;
  requested_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  resolution_note: string | null;
};

export type InvitationRead = {
  id: string;
  article_id: string;
  role: InvitationRole;
  email: string;
  status: InvitationStatus;
  invited_by: string;
  expires_at: string;
  review_due_at: string | null;
  created_at: string;
};

export type InvitationCreateResponse = {
  invitation: InvitationRead;
  warning: string | null;
};

export type AdminIssueReporter = {
  id: string;
  email: string;
  full_name: string | null;
};

export type AdminIssueRead = {
  id: string;
  user_id: string;
  title: string;
  description: string;
  status: IssueStatus;
  category: IssueCategory;
  upvote_count: number;
  reporter: AdminIssueReporter;
  images: IssueImage[];
  created_at: string;
  updated_at: string;
};

export type AdminIssueListParams = {
  status?: IssueStatus | null;
  category?: IssueCategory | null;
  sort?: "date" | "upvotes";
  direction?: "asc" | "desc";
};

export type McpAnalyticsPeriod = "24h" | "7d" | "30d" | "90d";
export type McpCallStatus = "success" | "error";

export type McpAnalyticsSummary = {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  average_duration_ms: number;
  commands_run: number;
  unique_users: number;
  previous_period_change_percent: number | null;
};

export type McpTimeBucket = {
  started_at: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
};

export type McpToolUsage = {
  tool_name: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  average_duration_ms: number;
  share_percent: number;
};

export type McpCommandUsage = {
  command_name: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  share_percent: number;
};

export type McpCommandGroupUsage = {
  key: string;
  total_calls: number;
  commands: McpCommandUsage[];
};

export type McpAnalyticsRead = {
  period: McpAnalyticsPeriod;
  starts_at: string;
  ends_at: string;
  bucket_granularity: "hour" | "day";
  summary: McpAnalyticsSummary;
  timeline: McpTimeBucket[];
  tools: McpToolUsage[];
  command_groups: McpCommandGroupUsage[];
};

export type McpCallActor = {
  id: string;
  email: string;
  full_name: string | null;
};

export type McpCallListItem = {
  id: string;
  created_at: string;
  actor: McpCallActor | null;
  trace_id: string | null;
  tool_name: string;
  command_name: string | null;
  status: McpCallStatus;
  duration_ms: number;
};

export type McpCallListRead = {
  items: McpCallListItem[];
  next_cursor: string | null;
};

export type McpCallDetailRead = McpCallListItem & {
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  error: string | null;
};

export type McpCallListParams = {
  period?: McpAnalyticsPeriod;
  tool?: string | null;
  command?: string | null;
  status?: McpCallStatus | null;
  cursor?: string | null;
  limit?: number;
};

type GetToken = () => Promise<string | null>;

export function listAdminArticles(
  getToken: GetToken,
  status?: VersionStatus | null,
) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<AdminArticleSummary[]>(
    `/api/v1/admin/articles${qs}`,
    getToken,
  );
}

export function getAdminArticle(getToken: GetToken, articleId: string) {
  return apiFetch<AdminArticleDetail>(
    `/api/v1/admin/articles/${articleId}`,
    getToken,
  );
}

export function assignReviewer(
  getToken: GetToken,
  articleId: string,
  userId: string,
  reviewDueAt?: string | null,
) {
  return apiFetch<{ ok: boolean; assignment_id: string }>(
    `/api/v1/admin/articles/${articleId}/assign-reviewer`,
    getToken,
    {
      method: "POST",
      body: JSON.stringify({ user_id: userId, review_due_at: reviewDueAt ?? null }),
    },
  );
}

export function assignEditor(
  getToken: GetToken,
  articleId: string,
  userId: string,
) {
  return apiFetch<{ ok: boolean; assignment_id: string }>(
    `/api/v1/admin/articles/${articleId}/assign-editor`,
    getToken,
    { method: "POST", body: JSON.stringify({ user_id: userId }) },
  );
}

export function unassignReviewer(
  getToken: GetToken,
  articleId: string,
  userId: string,
) {
  return apiFetch<void>(
    `/api/v1/admin/articles/${articleId}/reviewers/${userId}`,
    getToken,
    { method: "DELETE" },
  );
}

export function unassignEditor(
  getToken: GetToken,
  articleId: string,
  userId: string,
) {
  return apiFetch<void>(
    `/api/v1/admin/articles/${articleId}/editors/${userId}`,
    getToken,
    { method: "DELETE" },
  );
}

export function inviteToArticle(
  getToken: GetToken,
  articleId: string,
  email: string,
  role: InvitationRole,
  reviewDueAt?: string | null,
) {
  return apiFetch<InvitationCreateResponse>(
    `/api/v1/admin/articles/${articleId}/invite`,
    getToken,
    {
      method: "POST",
      body: JSON.stringify({ email, role, review_due_at: reviewDueAt ?? null }),
    },
  );
}

export function listArticleInvitations(getToken: GetToken, articleId: string) {
  return apiFetch<InvitationRead[]>(
    `/api/v1/admin/articles/${articleId}/invitations`,
    getToken,
  );
}

export function resendInvitation(getToken: GetToken, invitationId: string) {
  return apiFetch<{ ok: boolean; invitation_id: string }>(
    `/api/v1/admin/invitations/${invitationId}/resend`,
    getToken,
    { method: "POST" },
  );
}

export function cancelInvitation(getToken: GetToken, invitationId: string) {
  return apiFetch<void>(`/api/v1/admin/invitations/${invitationId}`, getToken, {
    method: "DELETE",
  });
}

export function overrideDecision(
  getToken: GetToken,
  articleId: string,
  status: VersionStatus,
  reason?: string | null,
) {
  return apiFetch<VersionRead>(
    `/api/v1/admin/articles/${articleId}/override-decision`,
    getToken,
    {
      method: "POST",
      body: JSON.stringify({ status, reason: reason ?? null }),
    },
  );
}

export function listAdminUsers(getToken: GetToken) {
  return apiFetch<AdminUserListItem[]>("/api/v1/admin/users", getToken);
}

export function listAppInvitations(getToken: GetToken) {
  return apiFetch<AppInvitationRead[]>("/api/v1/admin/invitations", getToken);
}

export function createAppInvitation(
  getToken: GetToken,
  payload: { email: string; full_name: string; gender: UserGender },
) {
  return apiFetch<AppInvitationCreateResponse>("/api/v1/admin/invitations", getToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function revokeAppInvitation(getToken: GetToken, invitationId: string) {
  return apiFetch<void>(
    `/api/v1/admin/invitations/${encodeURIComponent(invitationId)}/revoke`,
    getToken,
    { method: "POST" },
  );
}

export function resendAppInvitation(getToken: GetToken, invitationId: string) {
  return apiFetch<AppInvitationRead>(
    `/api/v1/admin/app-invitations/${encodeURIComponent(invitationId)}/resend`,
    getToken,
    { method: "POST" },
  );
}

export function listAccountDeletionRequests(getToken: GetToken) {
  return apiFetch<AccountDeletionRequestAdminRead[]>(
    "/api/v1/admin/account-deletion-requests",
    getToken,
  );
}

export function updateAccountDeletionRequest(
  getToken: GetToken,
  requestId: string,
  status: AccountDeletionRequestStatus,
  resolutionNote?: string | null,
) {
  return apiFetch<AccountDeletionRequestAdminRead>(
    `/api/v1/admin/account-deletion-requests/${requestId}`,
    getToken,
    {
      method: "PATCH",
      body: JSON.stringify({
        status,
        resolution_note: resolutionNote?.trim() || null,
      }),
    },
  );
}

export function listAdminIssues(
  getToken: GetToken,
  params: AdminIssueListParams = {},
) {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.category) search.set("category", params.category);
  if (params.sort) search.set("sort", params.sort);
  if (params.direction) search.set("direction", params.direction);
  const qs = search.toString();
  return apiFetch<AdminIssueRead[]>(
    `/api/v1/admin/issues${qs ? `?${qs}` : ""}`,
    getToken,
  );
}

export function updateIssueStatus(
  getToken: GetToken,
  issueId: string,
  status: IssueStatus,
) {
  return apiFetch<AdminIssueRead>(
    `/api/v1/admin/issues/${issueId}/status`,
    getToken,
    { method: "PATCH", body: JSON.stringify({ status }) },
  );
}

export function getMcpAnalytics(
  getToken: GetToken,
  period: McpAnalyticsPeriod = "7d",
) {
  return apiFetch<McpAnalyticsRead>(
    `/api/v1/admin/mcp/analytics?period=${encodeURIComponent(period)}`,
    getToken,
  );
}

export function listMcpCalls(
  getToken: GetToken,
  params: McpCallListParams = {},
) {
  return apiFetch<McpCallListRead>(buildMcpCallsPath(params), getToken);
}

export function getMcpCall(getToken: GetToken, callId: string) {
  return apiFetch<McpCallDetailRead>(
    `/api/v1/admin/mcp/calls/${encodeURIComponent(callId)}`,
    getToken,
  );
}

export const INVITATION_ROLE_LABELS: Record<InvitationRole, string> = {
  reviewer: "مراجع",
  editor: "محرر",
};

export const INVITATION_STATUS_LABELS: Record<InvitationStatus, string> = {
  pending: "معلّقة",
  accepted: "مقبولة",
  expired: "منتهية",
  cancelled: "ملغاة",
};

export const REVIEWER_STATUS_LABELS: Record<ReviewerAssignmentStatus, string> =
  {
    invited: "مدعو",
    accepted: "مقبول",
    declined: "مرفوض",
    completed: "مكتمل",
  };
