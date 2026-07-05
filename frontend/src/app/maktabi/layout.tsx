import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "مكتبي | البيان",
  description: "لوحة عمل المؤلف في مجلة البيان — إدارة المقالات والمسودات.",
};

export default function MaktabiLayout({ children }: { children: ReactNode }) {
  return children;
}
