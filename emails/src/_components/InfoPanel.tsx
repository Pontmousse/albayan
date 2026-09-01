import * as React from "react";
import { Section, Text } from "react-email";
import { colors, fontFamily } from "./theme";

type InfoPanelProps = {
  children: React.ReactNode;
};

export function InfoPanel({ children }: InfoPanelProps) {
  return (
    <Section
      className="email-info-panel"
      style={{
        backgroundColor: colors.white,
        border: `1px solid ${colors.border}`,
        borderRadius: "12px",
        margin: "22px 0",
        padding: "20px 24px",
      }}
    >
      <Text
        style={{
          color: colors.ink,
          fontFamily,
          fontSize: "17px",
          lineHeight: "2",
          margin: 0,
          textAlign: "center",
        }}
      >
        {children}
      </Text>
    </Section>
  );
}
