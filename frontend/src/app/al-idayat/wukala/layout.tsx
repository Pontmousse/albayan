import { DevModeGate } from "@/components/dev-mode-gate";
import { McpGate } from "@/components/mcp-gate";

export default function AgentTokensLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <McpGate>
      <DevModeGate>{children}</DevModeGate>
    </McpGate>
  );
}
