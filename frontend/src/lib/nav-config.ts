export type NavLink = { href: string; label: string; description?: string };

export type NavGroup = {
  label: string;
  items: NavLink[];
};

export const primaryNavLink: NavLink = { href: "/", label: "الرئيسية" };

export const navGroups: NavGroup[] = [
  {
    label: "للمؤلفين",
    items: [
      {
        href: "/irshadat-al-mualifin",
        label: "إرشادات المؤلفين",
        description: "كيفية تقديم البحث وإعداد المخطوطة",
      },
      {
        href: "/siyasat-an-nashr",
        label: "سياسة النشر",
        description: "معايير القبول والتحكيم والنشر المفتوح",
      },
    ],
  },
  {
    label: "عن المجلة",
    items: [
      {
        href: "/hayat-at-tahrir",
        label: "هيئة التحرير",
        description: "أعضاء التحرير والإشراف العلمي",
      },
      {
        href: "/al-siyasat-wal-shurut",
        label: "السياسات والشروط",
        description: "الأخلاقيات، الخصوصية، وشروط الاستخدام",
      },
    ],
  },
];

export const contactNavLink: NavLink = {
  href: "/al-tawasul",
  label: "التواصل",
};

export const footerLinks = {
  authors: [
    { href: "/irshadat-al-mualifin", label: "إرشادات المؤلفين" },
    { href: "/siyasat-an-nashr", label: "سياسة النشر" },
  ],
  about: [
    { href: "/hayat-at-tahrir", label: "هيئة التحرير" },
    { href: "/al-siyasat-wal-shurut", label: "السياسات والشروط" },
    { href: "/al-tawasul", label: "التواصل" },
  ],
};

export const contactEmail = "albayan@gmail.com";
