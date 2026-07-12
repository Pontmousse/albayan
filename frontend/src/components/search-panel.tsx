"use client";

export function SearchPanel() {
  return (
    <div className="space-y-4 rounded-xl border border-[var(--journal-border)] bg-white/80 p-4 shadow-sm sm:p-6">
      <h2 className="text-sm font-semibold text-slate-900">بحث في المحتوى المنشور</h2>
      <form
        className="space-y-3"
        role="search"
        aria-label="بحث في المجلة (واجهة فقط)"
        onSubmit={(e) => e.preventDefault()}
      >
        <label className="block text-xs font-medium text-slate-600" htmlFor="q">
          كلمات مفتاحية، عنوان، أو اسم مؤلف
        </label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            id="q"
            name="q"
            type="search"
            placeholder="مثال: تحكيم أقران، نشر مفتوح…"
            className="min-h-11 w-full rounded-md border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-[var(--journal-accent)] focus:ring-2 focus:ring-[var(--journal-accent)]/20"
          />
          <button
            type="submit"
            className="inline-flex min-h-11 shrink-0 items-center justify-center rounded-md bg-[var(--journal-accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)]"
          >
            بحث
          </button>
        </div>
        <p className="text-xs text-slate-500">
          سيتم ربط البحث لاحقاً بواجهة برمجة التطبيقات.
        </p>
      </form>
      <dl className="grid grid-cols-1 gap-3 border-t border-[var(--journal-border)] pt-4 text-xs text-slate-600 sm:grid-cols-3 sm:gap-4">
        <div>
          <dt className="font-medium text-slate-500">زمن التحكيم المستهدف</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">٤–٨ أسابيع</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">نموذج النشر</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">مفتوح الوصول</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">ISSN (قيد التسجيل)</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">XXXX-XXXX</dd>
        </div>
      </dl>
    </div>
  );
}
