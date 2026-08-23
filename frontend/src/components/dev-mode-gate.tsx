import { redirect } from "next/navigation";
import { isDevMode } from "@/lib/dev-mode";

/** يعيد التوجيه للرئيسية إن لم يكن وضع التطوير مفعّلاً. */
export function DevModeGate({ children }: { children: React.ReactNode }) {
  if (!isDevMode()) {
    redirect("/");
  }
  return children;
}
