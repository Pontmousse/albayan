import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DevMcpServerCarousel } from "./dev-mcp-server-carousel";
import { DEV_MCP_SERVERS } from "@/lib/dev-mcp-servers";

afterEach(() => vi.unstubAllEnvs());

describe("development MCP connectors", () => {
  it.each([undefined, "", "false", "0", "no"])(
    "renders no developer cards when dev mode is %s",
    (value) => {
      vi.stubEnv("NEXT_PUBLIC_DEV_MODE", value);
      expect(renderToStaticMarkup(<DevMcpServerCarousel />)).toBe("");
    },
  );

  it.each(["true", "1", "yes"])(
    "offers both connectors with copy controls and icon downloads when dev mode is %s",
    (value) => {
      vi.stubEnv("NEXT_PUBLIC_DEV_MODE", value);
      const html = renderToStaticMarkup(<DevMcpServerCarousel />);
      for (const server of DEV_MCP_SERVERS) {
        expect(html).toContain(server.name);
        expect(html).toContain(server.description);
        expect(html).toContain(server.url);
        expect(html).toContain(`href="${server.iconPath}"`);
        expect(html).toContain(`download="${server.filename}"`);
      }
      expect(html.match(/aria-label="نسخ اسم الاتصال"/g)).toHaveLength(2);
      expect(html.match(/aria-label="نسخ وصف الاتصال"/g)).toHaveLength(2);
      expect(html.match(/aria-label="نسخ عنوان خادم MCP"/g)).toHaveLength(2);
      expect(html).toContain('dir="rtl"');
      expect(html).toContain('aria-label="الموصل التالي"');
      expect(html).toContain('aria-label="الموصل السابق"');
    },
  );

  it("ships square transparent PNG icons below the strict 10,000-byte limit", () => {
    for (const server of DEV_MCP_SERVERS) {
      const png = readFileSync(resolve("public", server.iconPath.slice(1)));
      expect(png.length).toBeLessThan(10_000);
      expect(png.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
      expect(png.readUInt32BE(16)).toBe(png.readUInt32BE(20));
      // PNG palette transparency is stored in a tRNS chunk.
      expect(png.includes(Buffer.from("tRNS"))).toBe(true);
    }
  });
});
