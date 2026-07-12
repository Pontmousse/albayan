"use client";

import Link from "next/link";
import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { AdminShell } from "@/components/admin/admin-shell";
import { readClerkRole } from "@/lib/clerk-role";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, user } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.replace("/tawajjuh?next=%2Fadmin");
    }
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded) {
    return (
      <main className="mx-auto flex w-full max-w-3xl flex-1 items-center justify-center px-6 py-16">
        <p className="text-sm text-slate-500">جارٍ التحقق من الصلاحيات...</p>
      </main>
    );
  }

  if (!isSignedIn) {
    return (
      <main className="mx-auto flex w-full max-w-3xl flex-1 items-center justify-center px-6 py-16">
        <p className="text-sm text-slate-500">يتم تحويلك إلى صفحة تسجيل الدخول...</p>
      </main>
    );
  }

  if (readClerkRole(user.publicMetadata) !== "admin") {
    return (
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center gap-4 px-6 py-16 text-center">
        <h1 className="text-2xl font-bold text-slate-900">غير مصرح</h1>
        <p className="text-sm text-slate-600">
          هذه الصفحة مخصّصة للمستخدمين الذين لديهم دور مدير في Clerk فقط.
        </p>
        <Link
          href="/"
          className="rounded-md border border-[var(--journal-border)] bg-white px-4 py-2 text-sm font-semibold text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)]"
        >
          العودة إلى الصفحة الرئيسية
        </Link>
      </main>
    );
  }

  return <AdminShell>{children}</AdminShell>;
}
