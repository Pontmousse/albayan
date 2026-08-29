export type AdminSection = {
  id: string;
  label: string;
  href: string;
};

export const adminSections: AdminSection[] = [
  { id: "overview", label: "نظرة عامة", href: "/admin" },
  { id: "articles", label: "المقالات", href: "/admin/maqalat" },
  { id: "issues", label: "البلاغات", href: "/admin/balaghat" },
  { id: "users", label: "المستخدمون", href: "/admin/mustakhdimin" },
];
