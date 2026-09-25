"use client";

import Image from "next/image";
import { CopyButton } from "@/components/ui/copy-button";

export function ConnectionValue({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-emerald-200/80 bg-white/90 p-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold text-emerald-950">{label}</p>
          {hint ? (
            <p className="mt-0.5 text-[11px] leading-5 text-slate-500">{hint}</p>
          ) : null}
          <code
            dir="auto"
            className="mt-2 block break-all rounded-md bg-slate-100 px-2.5 py-2 text-start text-xs leading-5 text-slate-800"
          >
            {value}
          </code>
        </div>
        <CopyButton value={value} ariaLabel={`نسخ ${label}`} />
      </div>
    </div>
  );
}

export function ConnectorIconDownload({
  iconPath = "/connector_icon.png",
  name = "مجلة البيان",
  filename = "albayan-connector-icon.png",
}: {
  iconPath?: string;
  name?: string;
  filename?: string;
}) {
  return (
    <div className="rounded-xl border border-emerald-200/80 bg-white/90 p-3.5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-emerald-100 bg-white p-1.5 shadow-sm">
            <Image
              src={iconPath}
              alt={`أيقونة ${name} للموصل`}
              width={48}
              height={48}
              className="h-full w-full object-contain"
            />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-xs font-bold text-emerald-950">أيقونة الموصل</p>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-800 ring-1 ring-emerald-200">
                اختياري
              </span>
            </div>
            <p className="mt-1 text-[11px] leading-5 text-slate-500">
              حمّل شعار {name} المضغوط إذا كان برنامجك يدعم أيقونة مخصصة
              للموصل. الملف أقل من 10 كيلوبايت.
            </p>
          </div>
        </div>
        <a
          href={iconPath}
          download={filename}
          className="inline-flex shrink-0 items-center justify-center rounded-lg bg-emerald-700 px-3.5 py-2 text-xs font-bold text-white transition hover:bg-emerald-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2"
        >
          تحميل الأيقونة
        </a>
      </div>
    </div>
  );
}

