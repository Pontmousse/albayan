import { McpGate } from "@/components/mcp-gate";

export default function AgentTokensLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <McpGate>{children}</McpGate>;
}
