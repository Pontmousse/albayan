import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "استعادة كلمة المرور | البيان",
  description: "استعادة الوصول إلى حسابك في مجلة البيان.",
};

export default function PasswordRecoveryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
