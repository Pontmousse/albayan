"use client";

import Link from "next/link";
import { useClerk, useUser } from "@clerk/nextjs";
import { readClerkRole } from "@/lib/clerk-role";

export function AuthHeader() {
  const { isLoaded, isSignedIn, user } = useUser();
  const { signOut } = useClerk();

  if (!isLoaded) {
    return (
      <span className="text-xs text-slate-400" aria-hidden>
        …
      </span>
    );
  }

  if (!isSignedIn) {
    return (
      <Link
        href="/tawajjuh"
        className="rounded-md border border-amber-200 bg-white/80 px-3 py-1.5 text-xs font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)]"
      >
        تسجيل الدخول
      </Link>
    );
  }

  const displayName =
    user.fullName || user.firstName || user.primaryEmailAddress?.emailAddress || "حسابي";
  const isAdmin = readClerkRole(user.publicMetadata) === "admin";

  return (
    <div className="flex flex-wrap items-center justify-end gap-2 text-xs">
      <span className="font-medium text-slate-700">{displayName}</span>
      {isAdmin ? (
        <Link
          href="/admin"
          className="rounded-md px-2 py-1 font-semibold text-[var(--journal-accent)] underline-offset-4 hover:underline"
        >
          لوحة الإدارة
        </Link>
      ) : null}
      <Link
        href="/maktabi"
        className="rounded-md px-2 py-1 font-semibold text-[var(--journal-accent)] underline-offset-4 hover:underline"
      >
        مكتبي
      </Link>
      <Link
        href="/al-idayat"
        className="rounded-md px-2 py-1 text-[var(--journal-accent)] underline-offset-4 hover:underline"
      >
        إعدادات الحساب
      </Link>
      <button
        type="button"
        onClick={() => signOut({ redirectUrl: "/" })}
        className="rounded-md px-2 py-1 text-slate-500 underline-offset-4 hover:text-slate-800 hover:underline"
      >
        خروج
      </button>
    </div>
  );
}
