import Link from "next/link";

import { buttonClassName, cardClassName } from "@/lib/auth-ui";

type InvitationHandoffPageProps = {
  params: Promise<{ token: string }>;
  searchParams: Promise<{ status?: string | string[] }>;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function statusMessage(status: string | undefined): string | null {
  if (status === "expired") {
    return "انتهت صلاحية هذه الدعوة. اطلب من إدارة المجلة إرسال دعوة جديدة.";
  }
  if (status === "invalid") {
    return "هذه الدعوة غير صالحة أو لم تعد متاحة.";
  }
  if (status === "unavailable") {
    return "تعذّر التحقق من الدعوة حالياً. حاول مرة أخرى لاحقاً.";
  }
  return null;
}

export default async function InvitationHandoffPage({
  params,
  searchParams,
}: InvitationHandoffPageProps) {
  const { token } = await params;
  const query = await searchParams;
  const rawStatus = query.status;
  const status = Array.isArray(rawStatus) ? rawStatus[0] : rawStatus;
  const message = statusMessage(status);
  const action = `${API_BASE.replace(/\/$/, "")}/api/v1/public/app-invitations/${encodeURIComponent(token)}/continue`;

  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-10 sm:px-6">
        <div className={cardClassName}>
          <h1
            className="text-2xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            متابعة دعوة مجلة البيان
          </h1>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            لحماية رابط الدعوة من أنظمة فحص البريد الآلية، لن يتم فتح رابط القبول
            الحساس تلقائياً. اضغط الزر أدناه بنفسك للمتابعة إلى إنشاء الحساب.
          </p>

          {message ? (
            <p
              className="mt-5 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm leading-7 text-amber-900"
              role="alert"
            >
              {message}
            </p>
          ) : (
            <form method="post" action={action} className="mt-6">
              <button type="submit" className={`${buttonClassName} w-full`}>
                متابعة قبول الدعوة
              </button>
            </form>
          )}

          <p className="mt-6 text-center text-sm text-slate-600">
            <Link href="/" className="font-semibold text-[var(--journal-accent)] hover:underline">
              العودة إلى مجلة البيان
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
