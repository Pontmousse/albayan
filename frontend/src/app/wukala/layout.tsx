import { McpGate } from "@/components/mcp-gate";

export default function WukalaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <McpGate>{children}</McpGate>;
}
