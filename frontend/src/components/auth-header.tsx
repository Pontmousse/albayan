"use client";

import Link from "next/link";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { useClerk, useUser } from "@clerk/nextjs";
import { readClerkRole } from "@/lib/clerk-role";

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      aria-hidden
      className={`h-3.5 w-3.5 shrink-0 text-slate-500 transition-transform duration-200 ${
        open ? "rotate-180" : ""
      }`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

function MenuLink({
  href,
  label,
  onClick,
}: {
  href: string;
  label: string;
  onClick: () => void;
}) {
  return (
    <Link
      href={href}
      role="menuitem"
      onClick={onClick}
      className="flex min-h-11 items-center px-4 text-sm text-slate-700 transition-colors active:bg-[var(--journal-accent-soft)] hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
    >
      {label}
    </Link>
  );
}

export function AuthHeader() {
  const { isLoaded, isSignedIn, user } = useUser();
  const { signOut } = useClerk();
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => setOpen(false), []);

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
  }, [open, close]);

  if (!isLoaded) {
    return (
      <span className="inline-flex min-h-11 min-w-11 items-center justify-center text-xs text-slate-400" aria-hidden>
        …
      </span>
    );
  }

  if (!isSignedIn) {
    return (
      <Link
        href="/tawajjuh"
        className="inline-flex min-h-11 items-center rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-[var(--journal-accent)] transition active:bg-[var(--journal-accent-soft)] hover:bg-[var(--journal-accent-soft)]"
      >
        تسجيل الدخول
      </Link>
    );
  }

  const displayName =
    user.fullName ||
    user.firstName ||
    user.primaryEmailAddress?.emailAddress ||
    "حسابي";
  const isAdmin = readClerkRole(user.publicMetadata) === "admin";

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex min-h-11 max-w-[9.5rem] items-center gap-1.5 rounded-md border px-2.5 text-xs font-semibold transition sm:max-w-[12rem] ${
          open
            ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
            : "border-[var(--journal-border)] bg-white text-slate-700 active:bg-[var(--journal-accent-soft)] hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
        }`}
      >
        <span className="truncate sm:hidden">حسابي</span>
        <span className="hidden truncate sm:inline">{displayName}</span>
        <ChevronIcon open={open} />
      </button>

      <div
        id={panelId}
        role="menu"
        aria-label="قائمة الحساب"
        className={`absolute end-0 top-full z-50 mt-1.5 w-[min(16rem,calc(100vw-1.5rem))] overflow-hidden rounded-lg border border-[var(--journal-border)] bg-white shadow-md transition-all duration-150 ease-out ${
          open
            ? "pointer-events-auto translate-y-0 opacity-100"
            : "pointer-events-none -translate-y-1 opacity-0"
        }`}
      >
        <div className="border-b border-[var(--journal-border)] px-4 py-3">
          <p className="truncate text-sm font-semibold text-slate-800">
            {displayName}
          </p>
          {user.primaryEmailAddress?.emailAddress ? (
            <p className="mt-0.5 truncate text-xs text-slate-500">
              {user.primaryEmailAddress.emailAddress}
            </p>
          ) : null}
        </div>
        <div className="py-1">
          <MenuLink href="/maktabi" label="مكتبي" onClick={close} />
          {isAdmin ? (
            <MenuLink href="/admin" label="لوحة الإدارة" onClick={close} />
          ) : null}
          <MenuLink href="/al-idayat" label="إعدادات الحساب" onClick={close} />
        </div>
        <div className="border-t border-[var(--journal-border)] py-1">
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              close();
              void signOut({ redirectUrl: "/" });
            }}
            className="flex min-h-11 w-full items-center px-4 text-start text-sm text-slate-600 transition-colors active:bg-rose-50 hover:bg-rose-50 hover:text-rose-800"
          >
            خروج
          </button>
        </div>
      </div>
    </div>
  );
}
