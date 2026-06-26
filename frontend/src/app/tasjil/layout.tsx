import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "إنشاء حساب | البيان",
  description: "إنشاء حساب جديد في مجلة البيان.",
};

export default function SignUpLayout({ children }: { children: ReactNode }) {
  return children;
}
