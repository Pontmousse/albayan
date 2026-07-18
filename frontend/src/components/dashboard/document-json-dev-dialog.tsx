"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

function isPlainObject(value: unknown): value is Record<string, JsonValue> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function collectExpandablePaths(value: unknown, path: string, into: Set<string>): void {
  if (Array.isArray(value)) {
    if (value.length === 0) return;
    into.add(path);
    value.forEach((item, index) => {
      collectExpandablePaths(item, `${path}/${index}`, into);
    });
    return;
  }
  if (isPlainObject(value)) {
    const keys = Object.keys(value);
    if (keys.length === 0) return;
    into.add(path);
    for (const key of keys) {
      collectExpandablePaths(value[key], `${path}/${key}`, into);
    }
  }
}

function previewScalar(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "string") {
    const truncated =
      value.length > 80 ? `${value.slice(0, 80)}…` : value;
    return JSON.stringify(truncated);
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

function JsonNode({
  name,
  value,
  path,
  depth,
  expanded,
  onToggle,
}: {
  name?: string;
  value: unknown;
  path: string;
  depth: number;
  expanded: Set<string>;
  onToggle: (path: string) => void;
}) {
  const isArray = Array.isArray(value);
  const isObject = isPlainObject(value);
  const isExpandable =
    (isArray && value.length > 0) ||
    (isObject && Object.keys(value).length > 0);
  const open = isExpandable && expanded.has(path);

  if (!isExpandable) {
    return (
      <div className="font-mono text-xs leading-5" style={{ paddingInlineStart: depth * 12 }}>
        {name != null ? (
          <span className="text-sky-800">{JSON.stringify(name)}</span>
        ) : null}
        {name != null ? <span className="text-slate-400">: </span> : null}
        <span
          className={
            value === null
              ? "text-slate-500"
              : typeof value === "string"
                ? "text-emerald-800"
                : typeof value === "number"
                  ? "text-amber-800"
                  : typeof value === "boolean"
                    ? "text-violet-800"
                    : "text-slate-700"
          }
        >
          {previewScalar(value)}
        </span>
      </div>
    );
  }

  const entries = isArray
    ? value.map((item, index) => [String(index), item] as const)
    : Object.entries(value);
  const bracketOpen = isArray ? "[" : "{";
  const bracketClose = isArray ? "]" : "}";
  const summary = isArray ? `Array(${value.length})` : `Object(${entries.length})`;

  return (
    <div>
      <button
        type="button"
        onClick={() => onToggle(path)}
        className="flex w-full items-start gap-1 rounded px-0.5 text-start font-mono text-xs leading-5 hover:bg-slate-100"
        style={{ paddingInlineStart: depth * 12 }}
      >
        <span className="inline-block w-3 shrink-0 text-slate-500" aria-hidden>
          {open ? "▼" : "▶"}
        </span>
        {name != null ? (
          <>
            <span className="text-sky-800">{JSON.stringify(name)}</span>
            <span className="text-slate-400">: </span>
          </>
        ) : null}
        <span className="text-slate-600">{bracketOpen}</span>
        {!open ? (
          <span className="ms-1 text-slate-400">{summary} {bracketClose}</span>
        ) : null}
      </button>
      {open ? (
        <>
          {entries.map(([key, child]) => (
            <JsonNode
              key={`${path}/${key}`}
              name={key}
              value={child}
              path={`${path}/${key}`}
              depth={depth + 1}
              expanded={expanded}
              onToggle={onToggle}
            />
          ))}
          <div
            className="font-mono text-xs leading-5 text-slate-600"
            style={{ paddingInlineStart: depth * 12 + 16 }}
          >
            {bracketClose}
          </div>
        </>
      ) : null}
    </div>
  );
}

type Props = {
  open: boolean;
  value: unknown;
  onClose: () => void;
  title?: string;
};

export function DocumentJsonDevDialog({
  open,
  value,
  onClose,
  title = "تطوير / JSON المستند",
}: Props) {
  const allPaths = useMemo(() => {
    const paths = new Set<string>();
    collectExpandablePaths(value, "$", paths);
    return paths;
  }, [value]);

  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(["$"]));
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!open) return;
    // عند فتح الحوار فقط — لا نعيد الطي عند كل تحديث للمستند أثناء الفتح
    setExpanded(new Set(["$"]));
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const prettyText = useMemo(() => {
    try {
      return JSON.stringify(value ?? null, null, 2);
    } catch {
      return String(value);
    }
  }, [value]);

  const toggle = useCallback((path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }, []);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(prettyText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="document-json-dev-title"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-amber-300/80 bg-amber-50/95 shadow-lg"
        dir="ltr"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-amber-200 px-4 py-3">
          <h2
            id="document-json-dev-title"
            className="text-sm font-bold text-amber-900"
          >
            {title}
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setExpanded(new Set(allPaths))}
              className="min-h-8 rounded-md border border-amber-400 bg-white px-2.5 text-xs font-semibold text-amber-900 transition hover:bg-amber-100"
            >
              فتح الكل
            </button>
            <button
              type="button"
              onClick={() => setExpanded(new Set(["$"]))}
              className="min-h-8 rounded-md border border-amber-400 bg-white px-2.5 text-xs font-semibold text-amber-900 transition hover:bg-amber-100"
            >
              طي الكل
            </button>
            <button
              type="button"
              onClick={() => void handleCopy()}
              className="min-h-8 rounded-md border border-amber-400 bg-white px-2.5 text-xs font-semibold text-amber-900 transition hover:bg-amber-100"
            >
              {copied ? "تم النسخ" : "نسخ"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="min-h-8 rounded-md border border-slate-300 bg-white px-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              إغلاق
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto bg-white p-3 text-start">
          {value == null ? (
            <p className="font-mono text-xs text-slate-500">(لا يوجد مستند بعد)</p>
          ) : (
            <JsonNode
              value={value}
              path="$"
              depth={0}
              expanded={expanded}
              onToggle={toggle}
            />
          )}
        </div>
      </div>
    </div>
  );
}
