"use client";

export function SearchPanel() {
  return (
    <div className="space-y-4 rounded-xl border border-amber-200 bg-white/80 p-6 shadow-sm">
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
            placeholder="مثال: تحكيم أقران، نشر مفتوح، بيانات وصفية…"
            className="w-full rounded-md border border-amber-300 bg-white/90 px-3 py-2 text-sm text-slate-900 shadow-inner outline-none ring-[var(--journal-accent)] transition placeholder:text-slate-400 focus:border-[var(--journal-accent)] focus:ring-2"
          />
          <button
            type="submit"
            className="inline-flex shrink-0 items-center justify-center rounded-md bg-[var(--journal-accent)] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)]"
          >
            بحث
          </button>
        </div>
        <p className="text-xs text-slate-500">
          سيتم ربط البحث لاحقًا بواجهة برمجة التطبيقات في الخادم الخلفي إن شاء الله.
        </p>
      </form>
      <dl className="grid grid-cols-2 gap-4 border-t border-amber-100 pt-4 text-xs text-slate-600 sm:grid-cols-3">
        <div>
          <dt className="font-medium text-slate-500">زمن التحكيم المستهدف</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">٤–٨ أسابيع</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">نموذج النشر</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">مفتوح الوصول</dd>
        </div>
        <div className="col-span-2 sm:col-span-1">
          <dt className="font-medium text-slate-500">ISSN (قيد التسجيل إن شاء الله)</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">XXXX-XXXX</dd>
        </div>
      </dl>
    </div>
  );
}
