import type { Metadata } from "next";
import { ProfileForm } from "@/components/settings/profile-form";
import { SecurityForm } from "@/components/settings/security-form";
import { SimplePageFooter } from "@/components/simple-page-footer";

export const metadata: Metadata = {
  title: "إعدادات الحساب | البيان",
  description: "إدارة الملف الشخصي وإعدادات الأمان لحسابك في مجلة البيان.",
};

export default function SettingsPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          إعدادات الحساب
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          عدّل ملفك الشخصي وإعدادات الأمان المرتبطة بحسابك.
        </p>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <ProfileForm />
          <SecurityForm />
        </div>
      </main>
      <SimplePageFooter />
    </div>
  );
}
