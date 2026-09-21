"use client";

import Image from "next/image";
import Link from "next/link";
import {
  Bell,
  Bug,
  FileText,
  History,
  Home,
  ImageIcon,
  LayoutDashboard,
  Menu,
  Send,
  Settings,
  Sigma,
} from "lucide-react";
import {
  forwardRef,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  MobileSheet,
  mobileSheetOptionClassName,
} from "@/components/mobile-sheet";
import { NumeralToggle } from "@/components/numeral-toggle";
import { useMdUp } from "@/hooks/use-md-up";
import {
  contactNavLink,
  navGroups,
  primaryNavLink,
  supportNavLink,
} from "@/lib/nav-config";

type ArticleEditorHeaderProps = {
  articleTitle: string | null | undefined;
  ready: boolean;
  saveMessage: string | null;
  saveFailed: boolean;
  dirty: boolean;
  assetsUploading: boolean;
  resubmission: boolean;
  showDevJson: boolean;
  onBack: () => void;
  onOpenAssets: (returnFocus: HTMLElement) => void;
  onOpenEquationMappings: () => void;
  onOpenHistory: () => void;
  onOpenJson: () => void;
  onSubmit: () => void;
};

type MenuActionProps = {
  icon: React.ReactNode;
  label: string;
  onClick: (event: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  tone?: "default" | "gold" | "dev";
};

const menuOptionClassName = `${mobileSheetOptionClassName} border-0 bg-transparent text-slate-700 transition-colors hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)] disabled:cursor-not-allowed disabled:opacity-50 md:min-h-10 md:gap-2.5 md:px-3 md:py-2 md:text-sm md:font-medium md:leading-5`;

function MenuAction({
  icon,
  label,
  onClick,
  disabled = false,
  tone = "default",
}: MenuActionProps) {
  const toneClass =
    tone === "gold"
      ? "text-[var(--journal-gold)] hover:text-[var(--journal-gold)]"
      : tone === "dev"
        ? "text-amber-900 hover:bg-amber-50 hover:text-amber-950"
        : "";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${menuOptionClassName} ${toneClass}`}
    >
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white text-[var(--journal-accent)] shadow-sm ring-1 ring-[var(--journal-border)] md:h-7 md:w-7">
        {icon}
      </span>
      <span>{label}</span>
    </button>
  );
}

function MenuLink({
  href,
  label,
  icon,
  onClick,
}: {
  href: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={menuOptionClassName}
    >
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white text-[var(--journal-accent)] shadow-sm ring-1 ring-[var(--journal-border)] md:h-7 md:w-7">
        {icon}
      </span>
      <span>{label}</span>
    </Link>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <p className="px-5 pb-1 pt-4 text-xs font-bold uppercase tracking-wide text-slate-500 md:px-3 md:pb-1 md:pt-3">
      {children}
    </p>
  );
}

function SaveStatus({
  ready,
  saveMessage,
  saveFailed,
  dirty,
}: Pick<
  ArticleEditorHeaderProps,
  "ready" | "saveMessage" | "saveFailed" | "dirty"
>) {
  let compact = "جارٍ التحميل…";
  let full = "جارٍ تحميل المحرر…";
  let tone = "text-slate-500";

  if (ready) {
    if (saveFailed) {
      compact = "تعذّر الحفظ";
      full = saveMessage ?? "تعذّر الحفظ التلقائي.";
      tone = "text-red-700";
    } else if (saveMessage?.includes("جارٍ")) {
      compact = "جارٍ الحفظ…";
      full = saveMessage;
      tone = "text-slate-600";
    } else if (dirty) {
      compact = "غير محفوظ";
      full = "تغييرات غير محفوظة";
      tone = "text-[var(--journal-gold)]";
    } else {
      compact = "✓ محفوظ";
      full = saveMessage ?? "تم حفظ أحدث التغييرات.";
      tone = "text-emerald-700";
    }
  }

  return (
    <span
      className={`max-w-[6.75rem] shrink-0 truncate text-[11px] font-semibold sm:max-w-[11rem] sm:text-xs ${tone}`}
      role="status"
      title={full}
    >
      <span className="sm:hidden">{compact}</span>
      <span className="hidden sm:inline">{full}</span>
    </span>
  );
}

export const ArticleEditorHeader = forwardRef<
  HTMLDivElement,
  ArticleEditorHeaderProps
>(function ArticleEditorHeader(
  {
    articleTitle,
    ready,
    saveMessage,
    saveFailed,
    dirty,
    assetsUploading,
    resubmission,
    showDevJson,
    onBack,
    onOpenAssets,
    onOpenEquationMappings,
    onOpenHistory,
    onOpenJson,
    onSubmit,
  },
  ref,
) {
  const mdUp = useMdUp();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRootRef = useRef<HTMLDivElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  const closeMenu = useCallback(() => setMenuOpen(false), []);
  const journalLinks = useMemo(
    () => [
      primaryNavLink,
      ...navGroups.flatMap((group) => group.items),
      contactNavLink,
      supportNavLink,
    ],
    [],
  );

  useEffect(() => {
    if (!menuOpen || !mdUp) return;

    function onPointerDown(event: PointerEvent) {
      if (!menuRootRef.current?.contains(event.target as Node)) {
        closeMenu();
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closeMenu();
        menuButtonRef.current?.focus();
      }
    }

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [closeMenu, mdUp, menuOpen]);

  const menuContents = (
    <div className="pb-4 md:pb-2">
      <SectionTitle>أدوات المقال</SectionTitle>
      <div className="space-y-0.5 md:px-1">
        <MenuAction
          icon={<ImageIcon className="h-4 w-4" aria-hidden />}
          label={assetsUploading ? "جارٍ رفع الصور…" : "صور المقال وملفاته"}
          disabled={assetsUploading || !ready}
          onClick={(event) => {
            const returnFocus = event.currentTarget;
            closeMenu();
            onOpenAssets(returnFocus);
          }}
        />
        <MenuAction
          icon={<Sigma className="h-4 w-4" aria-hidden />}
          label="رموز المعادلات"
          disabled={!ready}
          onClick={() => {
            closeMenu();
            onOpenEquationMappings();
          }}
        />
        <MenuAction
          icon={<History className="h-4 w-4" aria-hidden />}
          label="سجل النسخ"
          disabled={!ready}
          onClick={() => {
            closeMenu();
            onOpenHistory();
          }}
        />
        {showDevJson ? (
          <MenuAction
            icon={<Bug className="h-4 w-4" aria-hidden />}
            label="عرض JSON"
            disabled={!ready}
            tone="dev"
            onClick={() => {
              closeMenu();
              onOpenJson();
            }}
          />
        ) : null}
        <MenuAction
          icon={<Send className="h-4 w-4" aria-hidden />}
          label={resubmission ? "إعادة تقديم المقال" : "تقديم المقال"}
          disabled={!ready}
          tone="gold"
          onClick={() => {
            closeMenu();
            onSubmit();
          }}
        />
      </div>

      <div className="mt-2 border-t border-[var(--journal-border)]">
        <SectionTitle>مساحة العمل</SectionTitle>
        <div className="space-y-0.5 md:px-1">
          <button
            type="button"
            onClick={() => {
              closeMenu();
              onBack();
            }}
            className={menuOptionClassName}
          >
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white text-[var(--journal-accent)] shadow-sm ring-1 ring-[var(--journal-border)] md:h-7 md:w-7">
              <FileText className="h-4 w-4" aria-hidden />
            </span>
            <span>تفاصيل المقال</span>
          </button>
          <MenuLink
            href="/maktabi"
            label="مكتبي"
            icon={<LayoutDashboard className="h-4 w-4" aria-hidden />}
            onClick={closeMenu}
          />
          <MenuLink
            href="/maktabi/maqalati"
            label="مقالاتي"
            icon={<FileText className="h-4 w-4" aria-hidden />}
            onClick={closeMenu}
          />
          <MenuLink
            href="/maktabi/isharat"
            label="الإشعارات"
            icon={<Bell className="h-4 w-4" aria-hidden />}
            onClick={closeMenu}
          />
          <MenuLink
            href="/al-idayat"
            label="إعدادات الحساب"
            icon={<Settings className="h-4 w-4" aria-hidden />}
            onClick={closeMenu}
          />
        </div>
      </div>

      <div className="mt-2 border-t border-[var(--journal-border)]">
        <SectionTitle>مجلة البيان</SectionTitle>
        <div className="space-y-0.5 md:px-1">
          {journalLinks.map((item) => (
            <MenuLink
              key={item.href}
              href={item.href}
              label={item.label}
              icon={<Home className="h-4 w-4" aria-hidden />}
              onClick={closeMenu}
            />
          ))}
        </div>
      </div>

      <div className="mt-2 border-t border-[var(--journal-border)]">
        {mdUp ? (
          <div className="flex items-center justify-between gap-3 px-3 py-3">
            <span className="text-xs font-semibold text-slate-600">شكل الأرقام</span>
            <NumeralToggle />
          </div>
        ) : (
          <NumeralToggle mobile />
        )}
      </div>
    </div>
  );

  return (
    <div
      ref={ref}
      className="article-editor__actions sticky top-0 z-40 border-b border-[var(--journal-border)] bg-[var(--journal-paper)]/95 pt-[env(safe-area-inset-top)] shadow-[0_1px_0_rgba(23,35,28,0.03)] backdrop-blur-md"
    >
      <div className="mx-auto flex min-h-14 w-full max-w-7xl items-center gap-2 px-2.5 py-1.5 sm:px-4 lg:px-6">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex min-h-10 min-w-10 shrink-0 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-2 text-sm font-semibold text-slate-700 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] sm:min-w-0 sm:gap-1.5 sm:px-3"
          aria-label="الرجوع إلى تفاصيل المقال"
        >
          <span aria-hidden>→</span>
          <span className="hidden sm:inline">رجوع</span>
        </button>

        <Link
          href="/"
          className="hidden shrink-0 items-center gap-1.5 rounded-md px-1.5 py-1 text-[var(--journal-accent)] transition hover:bg-[var(--journal-accent-soft)] sm:flex"
          aria-label="العودة إلى مجلة البيان"
        >
          <span className="albayan-logo-sweep relative block h-8 w-8 shrink-0 overflow-hidden rounded-full">
            <Image
              src="/official-logo.png"
              alt=""
              width={32}
              height={32}
              priority
              className="h-full w-full object-contain"
            />
          </span>
          <span
            className="hidden text-sm font-bold lg:inline"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            البيان
          </span>
        </Link>

        <div className="min-w-0 flex-1">
          <span className="block text-[10px] font-semibold text-slate-500 sm:hidden">
            تحرير المقال
          </span>
          <h1
            className="truncate text-sm font-bold text-slate-900 sm:text-base"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
            title={articleTitle ?? "المحرر"}
          >
            {articleTitle ?? "المحرر"}
          </h1>
        </div>

        <SaveStatus
          ready={ready}
          saveMessage={saveMessage}
          saveFailed={saveFailed}
          dirty={dirty}
        />

        <button
          type="button"
          onClick={onSubmit}
          disabled={!ready}
          className="hidden min-h-10 shrink-0 items-center gap-1.5 rounded-md border border-[var(--journal-gold)] bg-white px-3 text-xs font-semibold text-[var(--journal-gold)] transition hover:bg-[var(--journal-accent-soft)] disabled:cursor-not-allowed disabled:opacity-50 sm:inline-flex"
        >
          <Send className="h-4 w-4" aria-hidden />
          {resubmission ? "إعادة تقديم" : "تقديم"}
        </button>

        <div ref={menuRootRef} className="relative shrink-0">
          <button
            ref={menuButtonRef}
            type="button"
            aria-label="قائمة محرر المقال"
            aria-expanded={menuOpen}
            aria-haspopup="menu"
            onClick={() => setMenuOpen((value) => !value)}
            className={`inline-flex min-h-10 min-w-10 items-center justify-center rounded-md border transition ${
              menuOpen
                ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
                : "border-[var(--journal-border)] bg-white text-slate-700 hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
            }`}
          >
            <Menu className="h-5 w-5" aria-hidden />
          </button>

          <div
            role="menu"
            aria-label="قائمة محرر المقال"
            className={`dropdown-panel absolute end-0 top-full z-50 mt-1.5 hidden max-h-[min(76vh,42rem)] w-[min(23rem,calc(100vw-1.5rem))] overflow-y-auto overscroll-contain rounded-xl border border-[var(--journal-border)] bg-[var(--journal-paper)] shadow-xl md:block ${
              menuOpen
                ? "pointer-events-auto translate-y-0 opacity-100"
                : "pointer-events-none -translate-y-1 opacity-0"
            }`}
          >
            {menuContents}
          </div>
        </div>
      </div>

      <div className="md:hidden">
        <MobileSheet
          open={menuOpen && !mdUp}
          onClose={closeMenu}
          title="قائمة محرر المقال"
        >
          {menuContents}
        </MobileSheet>
      </div>
    </div>
  );
});
