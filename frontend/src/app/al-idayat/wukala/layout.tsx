import { DevModeGate } from "@/components/dev-mode-gate";

export default function AgentTokensLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DevModeGate>{children}</DevModeGate>;
}
