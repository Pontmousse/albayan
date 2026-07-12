"use client";

import { useSession, useSessionList, useUser } from "@clerk/nextjs";
import { FormEvent, useState } from "react";
import { buttonClassName, cardClassName, inputClassName, translateClerkError } from "@/lib/auth-ui";

function formatSessionDate(value: Date | null | undefined): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("ar", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(value);
}

export function SecurityForm() {
  const { user } = useUser();
  const { session: currentSession } = useSession();
  const { sessions, isLoaded } = useSessionList();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) return;

    if (newPassword !== confirmPassword) {
      setPasswordError("كلمة المرور الجديدة وتأكيدها غير متطابقين.");
      return;
    }

    setPasswordLoading(true);
    setPasswordMessage(null);
    setPasswordError(null);

    try {
      await user.updatePassword({ currentPassword, newPassword });
      setPasswordMessage("تم تحديث كلمة المرور بنجاح.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPasswordError(translateClerkError(err));
    } finally {
      setPasswordLoading(false);
    }
  }

  async function handleRevokeSession(sessionId: string) {
    const target = sessions?.find((item) => item.id === sessionId);
    if (!target) return;

    setRevokingId(sessionId);
    setSessionError(null);

    try {
      await target.end();
    } catch (err) {
      setSessionError(translateClerkError(err));
    } finally {
      setRevokingId(null);
    }
  }

  return (
    <section className={cardClassName}>
      <h2 className="text-lg font-bold text-[var(--journal-accent)]">الأمان</h2>

      <div className="mt-6">
        <h3 className="text-sm font-semibold text-slate-800">تغيير كلمة المرور</h3>
        <form onSubmit={handlePasswordSubmit} className="mt-3 space-y-3">
          <input
            type="password"
            autoComplete="current-password"
            placeholder="كلمة المرور الحالية"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className={inputClassName}
          />
          <input
            type="password"
            autoComplete="new-password"
            placeholder="كلمة المرور الجديدة"
            required
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className={inputClassName}
          />
          <input
            type="password"
            autoComplete="new-password"
            placeholder="تأكيد كلمة المرور الجديدة"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className={inputClassName}
          />

          {passwordMessage && (
            <p className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800" role="status">
              {passwordMessage}
            </p>
          )}
          {passwordError && (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
              {passwordError}
            </p>
          )}

          <button type="submit" disabled={passwordLoading} className={buttonClassName}>
            {passwordLoading ? "جارٍ التحديث…" : "تحديث كلمة المرور"}
          </button>
        </form>
      </div>

      <div className="mt-8 border-t border-[var(--journal-border)] pt-6">
        <h3 className="text-sm font-semibold text-slate-800">الجلسات النشطة</h3>
        {!isLoaded && <p className="mt-3 text-sm text-slate-500">جارٍ التحميل…</p>}
        {sessionError && (
          <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
            {sessionError}
          </p>
        )}
        <ul className="mt-3 space-y-3">
          {sessions?.map((session) => {
            const isCurrent = session.id === currentSession?.id;
            const label = isCurrent ? "هذا الجهاز" : `جلسة ${session.id.slice(-6)}`;

            return (
              <li
                key={session.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--journal-border)] bg-white/60 px-3 py-2 text-sm"
              >
                <div>
                  <p className="font-medium text-slate-800">
                    {label}
                    {isCurrent && (
                      <span className="ms-2 rounded bg-[var(--journal-accent-soft)] px-1.5 py-0.5 text-xs text-[var(--journal-accent-strong)]">
                        الجلسة الحالية
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-slate-500">
                    آخر نشاط: {formatSessionDate(session.lastActiveAt)}
                  </p>
                </div>
                {!isCurrent && (
                  <button
                    type="button"
                    disabled={revokingId === session.id}
                    onClick={() => void handleRevokeSession(session.id)}
                    className="text-xs font-semibold text-red-700 underline-offset-4 hover:underline disabled:opacity-50"
                  >
                    {revokingId === session.id ? "جارٍ الإنهاء…" : "إنهاء الجلسة"}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
