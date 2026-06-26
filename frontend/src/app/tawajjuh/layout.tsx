import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "تسجيل الدخول | البيان",
  description: "تسجيل الدخول إلى حسابك في مجلة البيان.",
};

export default function SignInLayout({ children }: { children: ReactNode }) {
  return children;
}
