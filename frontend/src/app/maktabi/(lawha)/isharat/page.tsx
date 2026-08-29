"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import {
  listNotificationsPage,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationRead,
} from "@/lib/api/notifications";
import { buttonClassName } from "@/lib/auth-ui";
import { formatRelativeTime } from "@/lib/format-date";

const PAGE_SIZE = 20;

export default function NotificationsPage() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<NotificationRead[] | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [mutatingId, setMutatingId] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFirstPage = useCallback(() => {
    setError(null);
    return listNotificationsPage(getToken, { limit: PAGE_SIZE })
      .then((page) => {
        setItems(page.items);
        setNextCursor(page.next_cursor);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "تعذّر تحميل الإشعارات.");
      });
  }, [getToken]);

  useEffect(() => {
    let cancelled = false;
    listNotificationsPage(getToken, { limit: PAGE_SIZE })
      .then((page) => {
        if (cancelled) return;
        setItems(page.items);
        setNextCursor(page.next_cursor);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تعذّر تحميل الإشعارات.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  async function handleLoadMore() {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    setError(null);
    try {
      const page = await listNotificationsPage(getToken, {
        limit: PAGE_SIZE,
        before: nextCursor,
      });
      setItems((rows) => [...(rows ?? []), ...page.items]);
      setNextCursor(page.next_cursor);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر تحميل المزيد.");
    } finally {
      setLoadingMore(false);
    }
  }

  async function handleMarkRead(notification: NotificationRead) {
    if (notification.is_read || mutatingId) return;
    const previous = items ?? [];
    setMutatingId(notification.id);
    setItems((rows) =>
      rows?.map((row) =>
        row.id === notification.id
          ? { ...row, is_read: true, read_at: new Date().toISOString() }
          : row,
      ) ?? rows,
    );
    setError(null);
    try {
      const updated = await markNotificationRead(getToken, notification.id);
      setItems((rows) =>
        rows?.map((row) => (row.id === updated.id ? updated : row)) ?? rows,
      );
    } catch (err) {
      setItems(previous);
      setError(err instanceof Error ? err.message : "تعذّر تحديث الإشعار.");
    } finally {
      setMutatingId(null);
    }
  }

  async function handleOpen(notification: NotificationRead) {
    await handleMarkRead(notification);
    if (notification.link) {
      router.push(notification.link);
    }
  }

  async function handleMarkAll() {
    const previous = items ?? [];
    setMarkingAll(true);
    setItems((rows) =>
      rows?.map((row) => ({
        ...row,
        is_read: true,
        read_at: row.read_at ?? new Date().toISOString(),
      })) ?? rows,
    );
    setError(null);
    try {
      await markAllNotificationsRead(getToken);
    } catch (err) {
      setItems(previous);
      setError(err instanceof Error ? err.message : "تعذّر تحديث الإشعارات.");
    } finally {
      setMarkingAll(false);
    }
  }

  const unreadCount = items?.filter((item) => !item.is_read).length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1
            className="text-3xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            الإشعارات
          </h1>
          <p className="mt-1.5 text-sm text-slate-600">
            آخر التنبيهات المرتبطة بحسابك.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void loadFirstPage()}
            className="rounded-md border border-[var(--journal-border)] bg-white px-4 py-2 text-sm font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)]"
          >
            تحديث
          </button>
          <button
            type="button"
            onClick={handleMarkAll}
            disabled={markingAll || unreadCount === 0}
            className={`${buttonClassName} disabled:cursor-not-allowed disabled:opacity-60`}
          >
            تعيين الكل كمقروء
          </button>
        </div>
      </div>

      {error ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {items === null && !error ? (
        <RowsSkeleton count={5} />
      ) : items !== null && items.length === 0 ? (
        <EmptyState
          title="لا توجد إشعارات"
          description="ستظهر هنا التنبيهات المهمة ونشاط البلاغات."
        />
      ) : items !== null ? (
        <div className="space-y-4">
          <ul className="space-y-2.5">
            {items.map((notification) => (
              <li key={notification.id}>
                <article
                  className={`rounded-lg border px-4 py-3.5 shadow-sm transition ${
                    notification.is_read
                      ? "border-[var(--journal-border)] bg-white/85"
                      : "border-emerald-200 bg-emerald-50/85"
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <button
                      type="button"
                      onClick={() => void handleOpen(notification)}
                      className="min-w-0 flex-1 text-start"
                    >
                      <h2 className="text-sm font-semibold text-slate-900">
                        {notification.title}
                      </h2>
                      {notification.body ? (
                        <p className="mt-1 text-sm leading-6 text-slate-600">
                          {notification.body}
                        </p>
                      ) : null}
                      <time
                        dateTime={notification.created_at}
                        className="mt-2 block text-xs text-slate-500"
                      >
                        {formatRelativeTime(notification.created_at)}
                      </time>
                    </button>
                    {!notification.is_read ? (
                      <button
                        type="button"
                        onClick={() => void handleMarkRead(notification)}
                        disabled={mutatingId === notification.id}
                        className="rounded-md border border-[var(--journal-border)] bg-white px-3 py-1.5 text-xs font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)] disabled:cursor-wait disabled:opacity-70"
                      >
                        تعيين كمقروء
                      </button>
                    ) : null}
                  </div>
                </article>
              </li>
            ))}
          </ul>

          {nextCursor ? (
            <div className="flex justify-center">
              <button
                type="button"
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="rounded-md border border-[var(--journal-border)] bg-white px-5 py-2 text-sm font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)] disabled:cursor-wait disabled:opacity-70"
              >
                {loadingMore ? "جارٍ التحميل..." : "تحميل المزيد"}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
