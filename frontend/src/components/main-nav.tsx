"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type RefObject,
} from "react";
import {
  contactNavLink,
  navGroups,
  primaryNavLink,
  type NavGroup,
} from "@/lib/nav-config";

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      aria-hidden
      className={`h-3.5 w-3.5 shrink-0 text-slate-500 transition-transform duration-200 ${
        open ? "rotate-180" : ""
      }`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

function useMenuDismiss(
  open: boolean,
  close: () => void,
  rootRef: RefObject<HTMLElement | null>,
) {
  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        close();
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, close, rootRef]);
}

function NavDropdown({ group }: { group: NavGroup }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const close = useCallback(() => setOpen(false), []);
  useMenuDismiss(open, close, rootRef);

  return (
    <div
      ref={rootRef}
      className="relative"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex min-h-10 items-center gap-1 rounded-md px-2.5 text-sm font-medium transition-colors duration-150 ${
          open
            ? "bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
            : "text-slate-700 hover:bg-[var(--journal-accent-soft)]/70 hover:text-[var(--journal-accent-strong)]"
        }`}
      >
        <span>{group.label}</span>
        <ChevronIcon open={open} />
      </button>

      <div
        id={panelId}
        role="menu"
        className={`absolute start-0 top-full z-50 mt-1.5 min-w-[14rem] overflow-hidden rounded-lg border border-[var(--journal-border)] bg-white shadow-md transition-all duration-150 ease-out ${
          open
            ? "pointer-events-auto translate-y-0 opacity-100"
            : "pointer-events-none -translate-y-1 opacity-0"
        }`}
      >
        <ul className="py-1">
          {group.items.map((item) => (
            <li key={item.href} role="none">
              <Link
                href={item.href}
                role="menuitem"
                onClick={close}
                className="block px-3.5 py-2.5 transition-colors duration-150 hover:bg-[var(--journal-accent-soft)]"
              >
                <span className="block text-sm font-medium text-slate-800">
                  {item.label}
                </span>
                {item.description ? (
                  <span className="mt-0.5 block text-xs leading-relaxed text-slate-500">
                    {item.description}
                  </span>
                ) : null}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function NavTextLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-10 items-center rounded-md px-2.5 text-sm font-medium text-slate-700 transition-colors duration-150 hover:bg-[var(--journal-accent-soft)]/70 hover:text-[var(--journal-accent-strong)]"
    >
      {label}
    </Link>
  );
}

/** قائمة موحّدة للشاشات الصغيرة */
function MobileNav() {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const close = useCallback(() => setOpen(false), []);
  useMenuDismiss(open, close, rootRef);

  const flatLinks = [
    primaryNavLink,
    ...navGroups.flatMap((g) => g.items),
    contactNavLink,
  ];

  return (
    <div ref={rootRef} className="relative md:hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label="قائمة التنقل"
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex min-h-11 items-center gap-1 rounded-md border px-3 text-xs font-semibold transition ${
          open
            ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
            : "border-[var(--journal-border)] bg-white text-slate-700 active:bg-[var(--journal-accent-soft)]"
        }`}
      >
        القائمة
        <ChevronIcon open={open} />
      </button>
      <div
        id={panelId}
        role="menu"
        className={`absolute end-0 top-full z-50 mt-1.5 w-[min(18rem,calc(100vw-1.25rem))] overflow-hidden rounded-lg border border-[var(--journal-border)] bg-white shadow-md transition-all duration-150 ${
          open
            ? "pointer-events-auto translate-y-0 opacity-100"
            : "pointer-events-none -translate-y-1 opacity-0"
        }`}
      >
        <ul className="max-h-[min(70vh,24rem)] overflow-y-auto overscroll-contain py-1">
          {flatLinks.map((item) => (
            <li key={item.href} role="none">
              <Link
                href={item.href}
                role="menuitem"
                onClick={close}
                className="flex min-h-11 items-center px-4 text-sm text-slate-700 active:bg-[var(--journal-accent-soft)] hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export function MainNav() {
  return (
    <>
      <MobileNav />
      <nav
        aria-label="التنقل الرئيسي"
        className="hidden items-center gap-0.5 md:flex"
      >
        <NavTextLink href={primaryNavLink.href} label={primaryNavLink.label} />
        {navGroups.map((group) => (
          <NavDropdown key={group.label} group={group} />
        ))}
        <NavTextLink href={contactNavLink.href} label={contactNavLink.label} />
      </nav>
    </>
  );
}
