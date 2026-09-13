"use client";

import { useAuth } from "@clerk/nextjs";
import {
  Activity,
  Braces,
  CheckCircle2,
  Clock3,
  TerminalSquare,
} from "lucide-react";
import {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  McpChartFrame,
  McpChartTooltip,
} from "@/components/admin/mcp-chart";
import { useNumerals } from "@/components/numeral-provider";
import {
  getMcpAnalytics,
  getMcpCall,
  listMcpCalls,
  type McpAnalyticsPeriod,
  type McpAnalyticsRead,
  type McpCallDetailRead,
  type McpCallListItem,
  type McpCallStatus,
} from "@/lib/api/admin";
import { userFacingErrorMessage } from "@/lib/user-facing-errors";

const PERIODS: Array<{ value: McpAnalyticsPeriod; label: string }> = [
  { value: "24h", label: "24 ساعة" },
  { value: "7d", label: "7 أيام" },
  { value: "30d", label: "30 يوماً" },
  { value: "90d", label: "كل السجل (90 يوماً)" },
];

const GROUP_LABELS: Record<string, string> = {
  block_editing: "تحرير الكتل",
  figures_floats: "الأشكال والعناصر العائمة",
  document_references: "بيانات المستند والمراجع",
  inline_tokens: "الرموز المضمّنة",
  lists: "القوائم",
  tables: "الجداول",
  other: "أوامر أخرى",
};

const STATUS_LABELS: Record<McpCallStatus, string> = {
  success: "ناجح",
  error: "خطأ",
};

function MetricCard({
  title,
  value,
  note,
  icon,
}: {
  title: string;
  value: string;
  note?: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-[var(--journal-border)] bg-white/85 p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-600">{title}</p>
          <p className="mt-2 text-3xl font-bold text-[var(--journal-accent-strong)]">
            {value}
          </p>
          {note ? <p className="mt-1 text-xs text-slate-500">{note}</p> : null}
        </div>
        <span className="rounded-lg bg-[var(--journal-accent-soft)] p-2 text-[var(--journal-accent)]">
          {icon}
        </span>
      </div>
    </div>
  );
}

function JsonSnapshot({ value }: { value: unknown }) {
  return (
    <pre
      dir="ltr"
      className="max-h-80 overflow-auto rounded-lg bg-slate-950 p-3 text-left font-mono text-xs leading-5 text-slate-100"
    >
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export default function AdminMcpAnalyticsPage() {
  const { getToken } = useAuth();
  const {
    formatAnalyticsBucket,
    formatDateTime,
    formatNumber,
  } = useNumerals();
  const [period, setPeriod] = useState<McpAnalyticsPeriod>("7d");
  const [analytics, setAnalytics] = useState<McpAnalyticsRead | null>(null);
  const [calls, setCalls] = useState<McpCallListItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [toolFilter, setToolFilter] = useState("");
  const [commandFilter, setCommandFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<"" | McpCallStatus>("");
  const [openCallId, setOpenCallId] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, McpCallDetailRead>>({});
  const [detailLoading, setDetailLoading] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const callParams = useMemo(
    () => ({
      period,
      tool: toolFilter || null,
      command: commandFilter || null,
      status: statusFilter || null,
      limit: 30,
    }),
    [commandFilter, period, statusFilter, toolFilter],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [analyticsResult, callsResult] = await Promise.all([
        getMcpAnalytics(getToken, period),
        listMcpCalls(getToken, callParams),
      ]);
      setAnalytics(analyticsResult);
      setCalls(callsResult.items);
      setNextCursor(callsResult.next_cursor);
      setOpenCallId(null);
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تحميل إحصاءات MCP."));
    } finally {
      setLoading(false);
    }
  }, [callParams, getToken, period]);

  useEffect(() => {
    void load();
  }, [load]);

  async function loadMore() {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const result = await listMcpCalls(getToken, {
        ...callParams,
        cursor: nextCursor,
      });
      setCalls((current) => [...current, ...result.items]);
      setNextCursor(result.next_cursor);
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تحميل المزيد من الاستدعاءات."));
    } finally {
      setLoadingMore(false);
    }
  }

  async function toggleDetail(callId: string) {
    if (openCallId === callId) {
      setOpenCallId(null);
      return;
    }
    setOpenCallId(callId);
    if (details[callId]) return;
    setDetailLoading(callId);
    try {
      const detail = await getMcpCall(getToken, callId);
      setDetails((current) => ({ ...current, [callId]: detail }));
    } catch (err) {
      setError(userFacingErrorMessage(err, "تعذّر تحميل تفاصيل الاستدعاء."));
      setOpenCallId(null);
    } finally {
      setDetailLoading(null);
    }
  }

  const commands = useMemo(
    () =>
      analytics?.command_groups.flatMap((group) => group.commands) ?? [],
    [analytics],
  );

  const change = analytics?.summary.previous_period_change_percent;
  const totalNote =
    change == null
      ? "لا تتوفر مقارنة للفترة المختارة"
      : `${change >= 0 ? "ارتفاع" : "انخفاض"} ${formatNumber(Math.abs(change))}% عن الفترة السابقة`;

  return (
    <div className="space-y-7">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1
            className="text-3xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            إحصاءات MCP
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm text-slate-600">
            استخدام أدوات الوكلاء وأوامر Document2، من لقطات منقّحة محفوظة لمدة 90 يوماً.
          </p>
        </div>
        <div className="flex flex-wrap rounded-lg border border-[var(--journal-border)] bg-white p-1" aria-label="الفترة الزمنية">
          {PERIODS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setPeriod(option.value)}
              aria-pressed={period === option.value}
              className={`rounded-md px-3 py-2 text-xs font-semibold transition sm:text-sm ${
                period === option.value
                  ? "bg-[var(--admin-accent)] text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </header>

      {error ? (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {loading && !analytics ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="جارٍ تحميل الإحصاءات">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-32 animate-pulse rounded-xl bg-slate-200/70" />
          ))}
        </div>
      ) : analytics ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard title="إجمالي الاستدعاءات" value={formatNumber(analytics.summary.total_calls)} note={totalNote} icon={<Activity className="size-5" aria-hidden />} />
            <MetricCard title="نسبة النجاح" value={`${formatNumber(analytics.summary.success_rate)}%`} note={`${formatNumber(analytics.summary.failed_calls)} أخطاء`} icon={<CheckCircle2 className="size-5" aria-hidden />} />
            <MetricCard title="متوسط المدة" value={`${formatNumber(analytics.summary.average_duration_ms)} مللي ثانية`} icon={<Clock3 className="size-5" aria-hidden />} />
            <MetricCard title="أوامر Document2" value={formatNumber(analytics.summary.commands_run)} note={`${formatNumber(analytics.summary.unique_users)} مستخدمين`} icon={<TerminalSquare className="size-5" aria-hidden />} />
          </section>

          <section className="grid gap-5 xl:grid-cols-5">
            <div className="rounded-xl border border-[var(--journal-border)] bg-white/85 p-4 shadow-sm xl:col-span-3">
              <h2 className="font-bold text-slate-800">الاستدعاءات عبر الزمن</h2>
              <p className="mt-1 text-xs text-slate-500">الناجحة والأخطاء لكل {analytics.bucket_granularity === "hour" ? "ساعة" : "يوم"}</p>
              <McpChartFrame label="مخطط زمني لاستدعاءات MCP" className="mt-4 h-72">
                <AreaChart data={analytics.timeline} margin={{ top: 8, right: 4, left: 0, bottom: 0 }} accessibilityLayer>
                  <defs>
                    <linearGradient id="mcp-success" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#0f766e" stopOpacity={0.35} /><stop offset="95%" stopColor="#0f766e" stopOpacity={0.04} /></linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="started_at" tickFormatter={(value) => formatAnalyticsBucket(String(value), analytics.bucket_granularity)} tick={{ fontSize: 11 }} minTickGap={24} reversed />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={35} orientation="right" />
                  <Tooltip content={(props) => <McpChartTooltip active={props.active} label={props.label} payload={props.payload} formatNumber={(value) => formatNumber(value)} formatLabel={(value) => formatDateTime(new Date(value))} />} />
                  <Area type="monotone" dataKey="successful_calls" name="ناجحة" stroke="#0f766e" fill="url(#mcp-success)" strokeWidth={2} />
                  <Area type="monotone" dataKey="failed_calls" name="أخطاء" stroke="#dc2626" fill="#fee2e2" strokeWidth={2} />
                </AreaChart>
              </McpChartFrame>
            </div>

            <div className="rounded-xl border border-[var(--journal-border)] bg-white/85 p-4 shadow-sm xl:col-span-2">
              <h2 className="font-bold text-slate-800">أكثر الأدوات استخداماً</h2>
              <p className="mt-1 text-xs text-slate-500">مرتبة بحسب عدد الاستدعاءات</p>
              {analytics.tools.length ? (
                <McpChartFrame label="ترتيب أدوات MCP" className="mt-4 h-72">
                  <BarChart data={analytics.tools.slice(0, 8)} layout="vertical" margin={{ top: 4, right: 8, left: 8, bottom: 4 }} accessibilityLayer>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                    <XAxis type="number" allowDecimals={false} />
                    <YAxis type="category" dataKey="tool_name" width={145} orientation="right" tick={{ fontSize: 10, fontFamily: "monospace" }} />
                    <Tooltip content={(props) => <McpChartTooltip active={props.active} label={props.label} payload={props.payload} formatNumber={(value) => formatNumber(value)} />} />
                    <Bar dataKey="total_calls" name="الاستدعاءات" fill="#1d4ed8" radius={[4, 4, 4, 4]} />
                  </BarChart>
                </McpChartFrame>
              ) : (
                <p className="mt-10 text-center text-sm text-slate-500">لا توجد استدعاءات في هذه الفترة.</p>
              )}
            </div>
          </section>

          <section>
            <div className="mb-3">
              <h2 className="text-lg font-bold text-slate-800">استخدام أوامر Document2</h2>
              <p className="mt-1 text-xs text-slate-500">تظهر كل الأوامر الحالية حتى إن لم تُستخدم بعد.</p>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {analytics.command_groups.map((group) => (
                <div key={group.key} className="rounded-xl border border-[var(--journal-border)] bg-white/85 p-4 shadow-sm">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-bold text-slate-800">{GROUP_LABELS[group.key] ?? group.key}</h3>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{formatNumber(group.total_calls)}</span>
                  </div>
                  <ul className="mt-3 space-y-2">
                    {group.commands.map((command) => {
                      const maximum = Math.max(...group.commands.map((item) => item.total_calls), 1);
                      return (
                        <li key={command.command_name}>
                          <div className="flex items-center justify-between gap-3 text-xs">
                            <code dir="ltr" className="truncate font-mono text-slate-700">{command.command_name}</code>
                            <span className="shrink-0 font-semibold text-slate-600">{formatNumber(command.total_calls)}</span>
                          </div>
                          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-[var(--admin-accent)]" style={{ width: `${(command.total_calls / maximum) * 100}%` }} /></div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-xl border border-[var(--journal-border)] bg-white/85 shadow-sm">
            <div className="border-b border-[var(--journal-border)] p-4">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-800">آخر النشاطات</h2>
                  <p className="mt-1 text-xs text-slate-500">افتح أي صف لمشاهدة اللقطة المنقّحة عند الطلب.</p>
                </div>
                <div className="grid w-full gap-2 sm:w-auto sm:grid-cols-3">
                  <label className="text-xs font-medium text-slate-600">الأداة<select dir="ltr" value={toolFilter} onChange={(event) => setToolFilter(event.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-left font-mono text-xs"><option value="">الكل</option>{analytics.tools.map((tool) => <option key={tool.tool_name} value={tool.tool_name}>{tool.tool_name}</option>)}</select></label>
                  <label className="text-xs font-medium text-slate-600">الأمر<select dir="ltr" value={commandFilter} onChange={(event) => setCommandFilter(event.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-left font-mono text-xs"><option value="">الكل</option>{commands.map((command) => <option key={command.command_name} value={command.command_name}>{command.command_name}</option>)}</select></label>
                  <label className="text-xs font-medium text-slate-600">الحالة<select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "" | McpCallStatus)} className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-xs"><option value="">الكل</option><option value="success">ناجح</option><option value="error">خطأ</option></select></label>
                </div>
              </div>
            </div>

            {calls.length === 0 ? (
              <p className="p-8 text-center text-sm text-slate-500">لا توجد استدعاءات مطابقة.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-sm">
                  <thead className="bg-slate-50 text-xs text-slate-600"><tr><th className="px-4 py-3 text-start">الوقت</th><th className="px-4 py-3 text-start">الأداة</th><th className="px-4 py-3 text-start">الأمر</th><th className="px-4 py-3 text-start">الفاعل</th><th className="px-4 py-3 text-start">الحالة</th><th className="px-4 py-3 text-start">المدة</th></tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {calls.map((call) => {
                      const detail = details[call.id];
                      const open = openCallId === call.id;
                      return (
                        <Fragment key={call.id}>
                          <tr className="hover:bg-slate-50">
                            <td className="px-4 py-3">
                              <button
                                type="button"
                                onClick={() => void toggleDetail(call.id)}
                                aria-expanded={open}
                                aria-controls={`mcp-call-${call.id}`}
                                className="text-start text-xs font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
                              >
                                <time dateTime={call.created_at}>
                                  {formatDateTime(new Date(call.created_at))}
                                </time>
                              </button>
                            </td>
                            <td className="max-w-48 px-4 py-3">
                              <code dir="ltr" className="block truncate font-mono text-xs text-slate-700">{call.tool_name}</code>
                            </td>
                            <td className="max-w-48 px-4 py-3">
                              <code dir="ltr" className="block truncate font-mono text-xs text-slate-600">{call.command_name ?? "—"}</code>
                            </td>
                            <td className="max-w-48 truncate px-4 py-3 text-xs text-slate-600">
                              {call.actor?.full_name || call.actor?.email || "مستخدم محذوف"}
                            </td>
                            <td className="px-4 py-3">
                              <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${call.status === "success" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{STATUS_LABELS[call.status]}</span>
                            </td>
                            <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-600">
                              {formatNumber(call.duration_ms)} م.ث
                            </td>
                          </tr>
                          {open ? (
                            <tr id={`mcp-call-${call.id}`}>
                              <td colSpan={6} className="border-t border-slate-100 bg-slate-50/70 p-4">
                                {detailLoading === call.id ? <p className="text-sm text-slate-500">جارٍ تحميل التفاصيل...</p> : detail ? (
                                  <div className="space-y-4">
                                    <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-600"><span>معرّف التتبع: <code dir="ltr" className="font-mono">{detail.trace_id ?? "—"}</code></span>{detail.error ? <span className="text-red-700">الخطأ: {detail.error}</span> : null}</div>
                                    <div className="grid gap-4 xl:grid-cols-2"><div><h4 className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-700"><Braces className="size-4" aria-hidden />المدخلات</h4><JsonSnapshot value={detail.input} /></div><div><h4 className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-700"><Braces className="size-4" aria-hidden />المخرجات</h4><JsonSnapshot value={detail.output} /></div></div>
                                  </div>
                                ) : null}
                              </td>
                            </tr>
                          ) : null}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
            {nextCursor ? <div className="border-t border-[var(--journal-border)] p-4 text-center"><button type="button" disabled={loadingMore} onClick={() => void loadMore()} className="rounded-md border border-[var(--journal-border)] bg-white px-4 py-2 text-sm font-semibold text-[var(--journal-accent)] disabled:opacity-50">{loadingMore ? "جارٍ التحميل..." : "تحميل المزيد"}</button></div> : null}
          </section>
        </>
      ) : null}
    </div>
  );
}
