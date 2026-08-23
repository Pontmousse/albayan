"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { buttonClassName } from "@/lib/auth-ui";

export function WukalaCtaButton({ className = "" }: { className?: string }) {
  const { isSignedIn } = useAuth();
  const router = useRouter();

  function handleClick() {
    if (isSignedIn) {
      router.push("/al-idayat/wukala");
      return;
    }
    router.push("/tawajjuh?next=/al-idayat/wukala");
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`${buttonClassName} ${className}`.trim()}
    >
      أنشئ مفتاحك الخاص
    </button>
  );
}
