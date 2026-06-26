"use client";

import Link from "next/link";
import { useCallback, useEffect, useId, useRef, useState } from "react";
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
      className={`h-4 w-4 shrink-0 text-slate-500 transition-transform duration-200 ${
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

function NavDropdown({ group }: { group: NavGroup }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        close();
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, close]);

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
        className={`group inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 ${
          open
            ? "bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)] shadow-sm"
            : "text-slate-700 hover:bg-white/80 hover:text-[var(--journal-accent-strong)]"
        }`}
      >
        <span>{group.label}</span>
        <ChevronIcon open={open} />
      </button>

      <div
        id={panelId}
        role="menu"
        className={`absolute start-0 top-full z-50 mt-1 min-w-[15rem] origin-top overflow-hidden rounded-xl border border-amber-200/90 bg-white/95 shadow-lg shadow-emerald-950/5 backdrop-blur-sm transition-all duration-200 ease-out ${
          open
            ? "pointer-events-auto translate-y-0 scale-100 opacity-100"
            : "pointer-events-none -translate-y-1 scale-[0.98] opacity-0"
        }`}
      >
        <ul className="py-1.5">
          {group.items.map((item) => (
            <li key={item.href} role="none">
              <Link
                href={item.href}
                role="menuitem"
                onClick={close}
                className="group/item block px-4 py-2.5 transition-colors duration-150 hover:bg-[var(--journal-accent-soft)]"
              >
                <span className="block text-sm font-semibold text-slate-800 group-hover/item:text-[var(--journal-accent-strong)]">
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
      className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 transition-all duration-200 hover:bg-white/80 hover:text-[var(--journal-accent-strong)]"
    >
      {label}
    </Link>
  );
}

export function MainNav() {
  return (
    <nav
      aria-label="التنقل الرئيسي"
      className="flex flex-wrap items-center justify-end gap-0.5 sm:gap-1"
    >
      <NavTextLink href={primaryNavLink.href} label={primaryNavLink.label} />
      {navGroups.map((group) => (
        <NavDropdown key={group.label} group={group} />
      ))}
      <NavTextLink href={contactNavLink.href} label={contactNavLink.label} />
    </nav>
  );
}
