import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  use: {
    baseURL: "http://127.0.0.1:3108",
    browserName: "chromium",
    launchOptions: { executablePath: "/usr/bin/google-chrome" },
  },
  webServer: {
    command: "npm run dev -- --hostname 0.0.0.0 --port 3108",
    url: "http://127.0.0.1:3108/al-durus",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
