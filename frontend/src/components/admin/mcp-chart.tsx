"use client";

import type { ReactNode } from "react";
import { ResponsiveContainer } from "recharts";

export function McpChartFrame({
  label,
  children,
  className = "h-72",
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      role="img"
      aria-label={label}
      className={`w-full min-w-0 ${className}`}
    >
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
}

export function McpChartTooltip({
  active,
  label,
  payload,
  formatNumber,
  formatLabel,
}: {
  active?: boolean;
  label?: string | number;
  payload?: ReadonlyArray<{
    color?: string;
    name?: string | number;
    value?: number | string | ReadonlyArray<number | string>;
  }>;
  formatNumber: (value: number) => string;
  formatLabel?: (value: string) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-lg">
      {label ? (
        <p className="mb-1 font-semibold text-slate-700">
          {formatLabel ? formatLabel(String(label)) : label}
        </p>
      ) : null}
      {payload.map((item) => (
        <div key={String(item.name)} className="flex items-center justify-between gap-5">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span
              className="size-2 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            {item.name}
          </span>
          <span className="font-semibold text-slate-900">
            {Array.isArray(item.value)
              ? item.value.map((value) => formatNumber(Number(value))).join(" – ")
              : formatNumber(Number(item.value ?? 0))}
          </span>
        </div>
      ))}
    </div>
  );
}
