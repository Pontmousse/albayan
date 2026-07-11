import { apiFetch } from "@/lib/api";
import type { VersionRead, VersionStatus } from "@/lib/api/articles";

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
  roles: string[];
  created_at: string;
};

export type InvitationRead = {
  id: string;
  article_id: string;
  role: InvitationRole;
  email: string;
  status: InvitationStatus;
  invited_by: string;
  expires_at: string;
  created_at: string;
};

export type InvitationCreateResponse = {
  invitation: InvitationRead;
  warning: string | null;
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
) {
  return apiFetch<{ ok: boolean; assignment_id: string }>(
    `/api/v1/admin/articles/${articleId}/assign-reviewer`,
    getToken,
    { method: "POST", body: JSON.stringify({ user_id: userId }) },
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
) {
  return apiFetch<InvitationCreateResponse>(
    `/api/v1/admin/articles/${articleId}/invite`,
    getToken,
    { method: "POST", body: JSON.stringify({ email, role }) },
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
