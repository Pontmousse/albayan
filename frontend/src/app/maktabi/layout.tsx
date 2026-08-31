import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "مكتبي | البيان",
  description:
    "مساحة عمل المستخدم في مجلة البيان، وتتكيف أقسامها مع أدواره ومهامه.",
};

export default function MaktabiLayout({ children }: { children: ReactNode }) {
  return children;
}
