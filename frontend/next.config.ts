import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Monorepo: repo root is parent of `frontend/` (avoids picking a stray lockfile higher in the tree)
  outputFileTracingRoot: path.join(__dirname, ".."),
};

export default nextConfig;
