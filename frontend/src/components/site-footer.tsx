import Link from "next/link";
import { contactEmail, footerLinks } from "@/lib/nav-config";

export function SiteFooter() {
  return (
    <footer className="border-t border-amber-200 bg-[#f3eadb]">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-10 sm:px-6 lg:flex-row lg:justify-between lg:px-8">
        <div className="max-w-md space-y-3 text-sm text-slate-600">
          <p className="text-base font-semibold text-slate-900">مجلة البيان</p>
          <p>
            منصة نشر علمي عربي تتبنى مبادئ النزاهة والشفافية وإتاحة المعرفة للمجتمع
            الأكاديمي والمهني.
          </p>
          <p className="inline-flex rounded-full border border-emerald-200 bg-emerald-50/80 px-3 py-1 text-xs font-medium text-[var(--journal-accent-strong)]">
            النشر مجاني — لا رسوم على المؤلفين
          </p>
        </div>

        <div className="grid grid-cols-2 gap-8 text-sm sm:grid-cols-3">
          <div>
            <p className="font-semibold text-slate-900">للمؤلفين</p>
            <ul className="mt-2 space-y-1.5">
              {footerLinks.authors.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-slate-600 transition-colors duration-150 hover:text-[var(--journal-accent-strong)]"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="font-semibold text-slate-900">عن المجلة</p>
            <ul className="mt-2 space-y-1.5">
              {footerLinks.about.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-slate-600 transition-colors duration-150 hover:text-[var(--journal-accent-strong)]"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="font-semibold text-slate-900">التواصل</p>
            <p className="mt-2">
              <a
                href={`mailto:${contactEmail}`}
                className="text-slate-600 transition-colors duration-150 hover:text-[var(--journal-accent-strong)]"
              >
                {contactEmail}
              </a>
            </p>
            <p className="mt-3 text-xs text-slate-500">
              ISSN: XXXX-XXXX (وهمي حتى اكتمال التسجيل إن شاء الله)
            </p>
          </div>
        </div>
      </div>
      <div className="border-t border-amber-200 bg-[#eadfca]">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-4 text-xs text-slate-600 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <p>© ١٤٤٧ هـ مجلة البيان. جميع الحقوق محفوظة.</p>
          <Link
            href="/al-siyasat-wal-shurut"
            className="transition-colors hover:text-[var(--journal-accent-strong)]"
          >
            السياسات والشروط
          </Link>
        </div>
      </div>
    </footer>
  );
}
