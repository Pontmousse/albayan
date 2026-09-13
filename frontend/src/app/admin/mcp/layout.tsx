import type { ReactNode } from "react";
import { McpGate } from "@/components/mcp-gate";

export default function AdminMcpLayout({ children }: { children: ReactNode }) {
  return <McpGate>{children}</McpGate>;
}
