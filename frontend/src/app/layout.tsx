import type { Metadata } from "next";
import { Amiri, Noto_Sans_Arabic } from "next/font/google";
import { AppClerkProvider } from "@/components/app-clerk-provider";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const notoSansArabic = Noto_Sans_Arabic({
  subsets: ["arabic"],
  variable: "--font-sans-ar",
  display: "swap",
});

const amiri = Amiri({
  weight: ["400", "700"],
  subsets: ["arabic"],
  variable: "--font-display-ar",
  display: "swap",
});

export const metadata: Metadata = {
  title: "البيان | مجلة علمية محكّمة",
  description:
    "مجلة علمية عربية للنشر المفتوح والبحث الخاضع للتحكيم الأقران في العلوم والهندسة والإنسانيات.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <body
        className={`${notoSansArabic.variable} ${amiri.variable} flex min-h-screen flex-col bg-white font-sans text-slate-900 antialiased`}
        style={{ fontFamily: "var(--font-sans-ar), system-ui, sans-serif" }}
      >
        <AppClerkProvider>
          <div className="flex flex-1 flex-col">
            <SiteHeader />
            {children}
            <SiteFooter />
          </div>
        </AppClerkProvider>
      </body>
    </html>
  );
}
