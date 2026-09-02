import type { Metadata } from "next";
import { Amiri, Noto_Sans_Arabic } from "next/font/google";
import { AppChrome } from "@/components/app-chrome";
import { AppClerkProvider } from "@/components/app-clerk-provider";
import { NumeralProvider } from "@/components/numeral-provider";
import { NUMERAL_STORAGE_KEY } from "@/lib/numerals";
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
  title: "مجلة البيان",
  icons: {
    icon: [
      {
        url: "/favicon.ico",
        type: "image/x-icon",
      },
    ],
    shortcut: "/favicon.ico",
    apple: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl" data-numeral-system="arab">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var n=localStorage.getItem(${JSON.stringify(NUMERAL_STORAGE_KEY)});if(n==="arab"||n==="latn")document.documentElement.dataset.numeralSystem=n}catch(e){}`,
          }}
        />
      </head>
      <body
        className={`${notoSansArabic.variable} ${amiri.variable} flex min-h-screen flex-col bg-white font-sans text-slate-900 antialiased`}
        style={{ fontFamily: "var(--font-sans-ar), system-ui, sans-serif" }}
      >
        <NumeralProvider>
          <AppClerkProvider>
            <AppChrome>{children}</AppChrome>
          </AppClerkProvider>
        </NumeralProvider>
      </body>
    </html>
  );
}
