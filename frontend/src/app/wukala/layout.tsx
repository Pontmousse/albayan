import { DevModeGate } from "@/components/dev-mode-gate";

export default function WukalaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DevModeGate>{children}</DevModeGate>;
}
