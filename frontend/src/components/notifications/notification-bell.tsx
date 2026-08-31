"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { MobileSheet } from "@/components/mobile-sheet";
import { useMdUp } from "@/hooks/use-md-up";
import {
  getUnreadNotificationCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationRead,
} from "@/lib/api/notifications";
import { formatRelativeTime } from "@/lib/format-date";

function BellIcon() {
  return (
    <svg
      aria-hidden
      className="h-5 w-5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.8}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9a6 6 0 1 0-12 0v.75a8.967 8.967 0 0 1-2.312 6.022 23.848 23.848 0 0 0 5.455 1.31m5.714 0a3 3 0 0 1-5.714 0"
      />
    </svg>
  );
}

function NotificationRows({
  notifications,
  loading,
  error,
  onItemClick,
}: {
  notifications: NotificationRead[];
  loading: boolean;
  error: string | null;
  onItemClick: (notification: NotificationRead) => void;
}) {
  if (loading) {
    return (
      <div className="space-y-2 p-3">
        {[0, 1, 2].map((item) => (
          <div
            key={item}
            className="h-14 animate-pulse rounded-md bg-slate-100"
            aria-hidden
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="px-4 py-5 text-sm leading-6 text-red-700" role="alert">
        {error}
      </p>
    );
  }

  if (notifications.length === 0) {
    return (
      <p className="px-4 py-7 text-center text-sm text-slate-500">
        لا توجد إشعارات بعد
      </p>
    );
  }

  return (
    <ul className="max-h-[22rem] overflow-y-auto py-1">
      {notifications.map((notification) => (
        <li key={notification.id}>
          <button
            type="button"
            onClick={() => onItemClick(notification)}
            className={`block w-full px-4 py-3 text-start transition-colors ${
              notification.is_read
                ? "bg-white text-slate-700 hover:bg-[var(--journal-accent-soft)]"
                : "bg-emerald-50/80 text-slate-900 hover:bg-emerald-100/70"
            }`}
          >
            <span className="flex items-start gap-2">
              {!notification.is_read ? (
                <span
                  className="mt-2 h-2 w-2 shrink-0 rounded-full bg-[var(--journal-accent)]"
                  aria-hidden
                />
              ) : null}
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-semibold">
                  {notification.title}
                </span>
                {notification.body ? (
                  <span className="mt-0.5 line-clamp-2 block text-xs leading-5 text-slate-600">
                    {notification.body}
                  </span>
                ) : null}
                <time
                  dateTime={notification.created_at}
                  className="mt-1 block text-xs text-slate-500"
                >
                  {formatRelativeTime(notification.created_at)}
                </time>
              </span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

export function NotificationBell() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const router = useRouter();
  const mdUp = useMdUp();
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [count, setCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sheetOpen = open && !mdUp;

  const close = useCallback(() => {
    setOpen(false);
    window.setTimeout(() => buttonRef.current?.focus(), 0);
  }, []);

  const refreshCount = useCallback(() => {
    if (!isSignedIn) return;
    getUnreadNotificationCount(getToken)
      .then((data) => setCount(data.count))
      .catch(() => setCount(0));
  }, [getToken, isSignedIn]);

  const loadNotifications = useCallback(() => {
    if (!isSignedIn) return;
    setLoading(true);
    setError(null);
    Promise.all([
      listNotifications(getToken, 10),
      getUnreadNotificationCount(getToken),
    ])
      .then(([rows, unread]) => {
        setNotifications(rows);
        setCount(unread.count);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "تعذّر تحميل الإشعارات.");
      })
      .finally(() => setLoading(false));
  }, [getToken, isSignedIn]);

  useEffect(() => {
    if (isLoaded && isSignedIn) refreshCount();
  }, [isLoaded, isSignedIn, refreshCount]);

  useEffect(() => {
    if (open) loadNotifications();
  }, [loadNotifications, open]);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        close();
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [close, open]);

  if (!isLoaded || !isSignedIn) return null;

  async function handleMarkAllRead() {
    const previous = notifications;
    setNotifications((rows) => rows.map((row) => ({ ...row, is_read: true })));
    setCount(0);
    try {
      await markAllNotificationsRead(getToken);
    } catch (err) {
      setNotifications(previous);
      setCount(previous.filter((row) => !row.is_read).length);
      setError(err instanceof Error ? err.message : "تعذّر تحديث الإشعارات.");
    }
  }

  async function handleItemClick(notification: NotificationRead) {
    close();
    if (!notification.is_read) {
      setNotifications((rows) =>
        rows.map((row) =>
          row.id === notification.id ? { ...row, is_read: true } : row,
        ),
      );
      setCount((value) => Math.max(0, value - 1));
      markNotificationRead(getToken, notification.id).catch(refreshCount);
    }
    if (notification.link) {
      router.push(notification.link);
    }
  }

  const panel = (
    <>
      <div className="flex items-center justify-between gap-3 border-b border-[var(--journal-border)] px-4 py-3">
        <h2
          className="text-base font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          الإشعارات
        </h2>
        <button
          type="button"
          onClick={handleMarkAllRead}
          disabled={count === 0}
          className="rounded-md px-2 py-1 text-xs font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)] disabled:cursor-not-allowed disabled:text-slate-400"
        >
          تعيين الكل كمقروء
        </button>
      </div>
      <NotificationRows
        notifications={notifications}
        loading={loading}
        error={error}
        onItemClick={handleItemClick}
      />
      <div className="border-t border-[var(--journal-border)] px-4 py-2">
        <Link
          href="/maktabi/isharat"
          onClick={close}
          className="block rounded-md px-2 py-2 text-center text-sm font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)]"
        >
          عرض جميع الإشعارات
        </Link>
      </div>
    </>
  );

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={buttonRef}
        type="button"
        aria-label="الإشعارات"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
        className={`relative inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border transition ${
          open
            ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
            : "border-[var(--journal-border)] bg-white text-slate-700 active:bg-[var(--journal-accent-soft)] hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
        }`}
      >
        <BellIcon />
        {count > 0 ? (
          <span className="absolute -end-1 -top-1 min-w-5 rounded-full bg-red-600 px-1.5 py-0.5 text-center text-[10px] font-bold leading-none text-white">
            {count > 99 ? "99+" : count}
          </span>
        ) : null}
      </button>

      <div className="md:hidden">
        <MobileSheet open={sheetOpen} onClose={close} title="الإشعارات">
          {panel}
        </MobileSheet>
      </div>

      <div
        id={panelId}
        className={`dropdown-panel absolute start-0 top-full z-50 mt-1.5 hidden w-[min(22rem,calc(100vw-1.5rem))] overflow-hidden rounded-lg border border-[var(--journal-border)] bg-white shadow-md md:block ${
          open
            ? "pointer-events-auto translate-y-0 opacity-100"
            : "pointer-events-none -translate-y-1 opacity-0"
        }`}
      >
        {panel}
      </div>
    </div>
  );
}
