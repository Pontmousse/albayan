import { redirect } from "next/navigation";
import { isMcpEnabled } from "@/lib/mcp-enabled";

/** يعيد التوجيه للرئيسية إن لم تكن ميزة MCP مفعّلة. */
export function McpGate({ children }: { children: React.ReactNode }) {
  if (!isMcpEnabled()) {
    redirect("/");
  }
  return children;
}
