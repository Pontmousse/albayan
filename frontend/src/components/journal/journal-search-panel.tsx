"use client";

/**
 * لوحة بحث المجلة — محفوظة لإعادة الاستخدام عند ربط واجهة بحث حقيقية.
 * لا تُعرض في الرئيسية حتى يتوفر API بحث ومقالات قابلة للفهرسة.
 * تحذير للوكلاء: لا تُضاف ISSN أو DOI أو إحصاءات وهمية هنا.
 */
export function JournalSearchPanel() {
  return (
    <div className="space-y-4 rounded-xl border border-[var(--journal-border)] bg-white/80 p-4 shadow-sm sm:p-6">
      <h2 className="text-sm font-semibold text-slate-900">بحث في المحتوى المنشور</h2>
      <p className="text-sm leading-7 text-slate-600">
        محرك البحث سيُفعَّل عند توفر مقالات منشورة وفهرسة حقيقية من الخادم.
      </p>
    </div>
  );
}
