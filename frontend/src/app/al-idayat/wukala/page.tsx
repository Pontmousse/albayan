import type { Metadata } from "next";
import { AgentTokensPanel } from "@/components/settings/agent-tokens-panel";

export const metadata: Metadata = {
  title: "مفاتيح الوكلاء المتقدمة | البيان",
  description: "إدارة مفاتيح الوكلاء للتطوير والربط المحلي غير التفاعلي.",
};

export default function AgentTokensPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          مفاتيح الوكلاء المتقدمة
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          مفاتيح شخصية للتطوير والأتمتة غير التفاعلية والربط المحلي. للاستخدام
          المعتاد، استخدم خادم البيان البعيد وسجّل الدخول عبر برنامجك.
        </p>
        <div className="mt-8">
          <AgentTokensPanel />
        </div>
      </main>
    </div>
  );
}
