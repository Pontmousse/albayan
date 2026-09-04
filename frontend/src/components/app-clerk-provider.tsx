"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { arSA } from "@clerk/localizations";
import type { ReactNode } from "react";

/**
 * Code-side auth path config (preferred long-term over Dashboard-only Paths).
 * Sign-in / sign-up already use NEXT_PUBLIC_CLERK_*_URL; consent routing to
 * /oauth-consent is still set in Clerk Dashboard → Paths until Clerk exposes
 * an equivalent env/prop for OAuth consent.
 */
export function AppClerkProvider({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider
      localization={arSA}
      signInUrl={process.env.NEXT_PUBLIC_CLERK_SIGN_IN_URL || "/tawajjuh"}
      signUpUrl={process.env.NEXT_PUBLIC_CLERK_SIGN_UP_URL || "/tasjil"}
      signInFallbackRedirectUrl={
        process.env.NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL || "/"
      }
      signUpFallbackRedirectUrl={
        process.env.NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL || "/"
      }
    >
      {children}
    </ClerkProvider>
  );
}
