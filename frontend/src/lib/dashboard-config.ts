export type DashboardRole = "author" | "reviewer" | "editor" | "admin";

export type DashboardSection = {
  id: string;
  label: string;
  href: string;
  roles: DashboardRole[];
};

export const dashboardSections: DashboardSection[] = [
  {
    id: "overview",
    label: "نظرة عامة",
    href: "/maktabi",
    roles: ["author", "reviewer", "editor", "admin"],
  },
  {
    id: "articles",
    label: "مقالاتي",
    href: "/maktabi/maqalati",
    roles: ["author", "admin"],
  },
  {
    id: "notifications",
    label: "الإشعارات",
    href: "/maktabi/isharat",
    roles: ["author", "reviewer", "editor", "admin"],
  },
  {
    id: "reviews",
    label: "مراجعاتي",
    href: "/maktabi/murajaati",
    roles: ["reviewer"],
  },
  {
    id: "editing",
    label: "تحريري",
    href: "/maktabi/tahriri",
    roles: ["editor"],
  },
  {
    id: "admin",
    label: "إدارة",
    href: "/admin",
    roles: ["admin"],
  },
];

export function visibleSections(roles: DashboardRole[]) {
  return dashboardSections.filter((section) =>
    section.roles.some((role) => roles.includes(role)),
  );
}
