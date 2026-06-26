"use client";

import { ClerkProvider } from "@clerk/nextjs";
import type { ReactNode } from "react";

export function AppClerkProvider({ children }: { children: ReactNode }) {
  return <ClerkProvider>{children}</ClerkProvider>;
}
