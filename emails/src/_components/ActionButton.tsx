import * as React from "react";
import { Button, Section } from "react-email";
import { colors, fontFamily } from "./theme";

type ActionButtonProps = {
  href: string;
  children: React.ReactNode;
};

export function ActionButton({ href, children }: ActionButtonProps) {
  return (
    <Section style={{ textAlign: "center", padding: "10px 0 18px" }}>
      <Button
        className="email-action-button"
        href={href}
        style={{
          backgroundColor: colors.accentStrong,
          border: `1px solid ${colors.accent}`,
          borderRadius: "10px",
          color: colors.white,
          boxSizing: "border-box",
          display: "inline-block",
          fontFamily,
          fontSize: "18px",
          fontWeight: 700,
          lineHeight: "24px",
          maxWidth: "100%",
          padding: "14px 34px",
          textDecoration: "none",
        }}
      >
        {children}
      </Button>
    </Section>
  );
}
