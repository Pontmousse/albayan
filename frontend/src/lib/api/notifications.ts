import { apiFetch } from "@/lib/api";

export type NotificationType =
  | "system"
  | "mention"
  | "issue_reply"
  | "issue_upvoted"
  | "issue_status_changed";

export type NotificationActor = {
  id: string;
  full_name: string | null;
};

export type NotificationRead = {
  id: string;
  type: NotificationType;
  title: string;
  body: string | null;
  link: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  actor: NotificationActor | null;
  metadata: Record<string, unknown>;
};

type GetToken = () => Promise<string | null>;

export function listNotifications(getToken: GetToken, limit = 10) {
  const qs = `?limit=${encodeURIComponent(String(limit))}`;
  return apiFetch<NotificationRead[]>(`/api/v1/notifications${qs}`, getToken);
}

export function getUnreadNotificationCount(getToken: GetToken) {
  return apiFetch<{ count: number }>(
    "/api/v1/notifications/unread-count",
    getToken,
  );
}

export function markNotificationRead(getToken: GetToken, id: string) {
  return apiFetch<NotificationRead>(
    `/api/v1/notifications/${id}/read`,
    getToken,
    { method: "PATCH" },
  );
}

export function markAllNotificationsRead(getToken: GetToken) {
  return apiFetch<{ ok: boolean; updated: number }>(
    "/api/v1/notifications/read-all",
    getToken,
    { method: "PATCH" },
  );
}
