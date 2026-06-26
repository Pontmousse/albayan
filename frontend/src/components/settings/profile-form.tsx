"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { getCurrentUser, updateCurrentUser } from "@/lib/api";
import { buttonClassName, cardClassName, inputClassName } from "@/lib/auth-ui";

export function ProfileForm() {
  const { getToken } = useAuth();
  const { user } = useUser();
  const [fullName, setFullName] = useState("");
  const [affiliation, setAffiliation] = useState("");
  const [bio, setBio] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = await getCurrentUser(getToken);
      setFullName(profile.full_name ?? "");
      setAffiliation(profile.affiliation ?? "");
      setBio(profile.bio ?? "");
      setEmail(profile.email);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر تحميل الملف الشخصي.");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    if (user?.primaryEmailAddress?.emailAddress && !email) {
      setEmail(user.primaryEmailAddress.emailAddress);
    }
  }, [user, email]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);

    try {
      await updateCurrentUser(getToken, {
        full_name: fullName.trim() || null,
        affiliation: affiliation.trim() || null,
        bio: bio.trim() || null,
      });
      setMessage("تم الحفظ بنجاح.");
      await loadProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر حفظ التغييرات.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className={cardClassName}>
        <h2 className="text-lg font-bold text-[var(--journal-accent)]">الملف الشخصي</h2>
        <p className="mt-4 text-sm text-slate-500">جارٍ التحميل…</p>
      </section>
    );
  }

  return (
    <section className={cardClassName}>
      <h2 className="text-lg font-bold text-[var(--journal-accent)]">الملف الشخصي</h2>
      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div>
          <label htmlFor="fullName" className="mb-1 block text-sm font-medium text-slate-700">
            الاسم الكامل
          </label>
          <input
            id="fullName"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className={inputClassName}
          />
        </div>
        <div>
          <label htmlFor="affiliation" className="mb-1 block text-sm font-medium text-slate-700">
            الانتماء المؤسسي
          </label>
          <input
            id="affiliation"
            type="text"
            placeholder="مثال: جامعة الملك سعود"
            value={affiliation}
            onChange={(e) => setAffiliation(e.target.value)}
            className={inputClassName}
          />
        </div>
        <div>
          <label htmlFor="bio" className="mb-1 block text-sm font-medium text-slate-700">
            نبذة قصيرة
          </label>
          <textarea
            id="bio"
            rows={4}
            maxLength={500}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            className={inputClassName}
          />
          <p className="mt-1 text-xs text-slate-500">{bio.length}/500</p>
        </div>
        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
            البريد الإلكتروني
          </label>
          <input
            id="email"
            type="email"
            value={email}
            readOnly
            className={`${inputClassName} bg-slate-50 text-slate-500`}
          />
        </div>

        {message && (
          <p className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800" role="status">
            {message}
          </p>
        )}
        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
            {error}
          </p>
        )}

        <button type="submit" disabled={saving} className={buttonClassName}>
          {saving ? "جارٍ الحفظ…" : "حفظ التغييرات"}
        </button>
      </form>
    </section>
  );
}
