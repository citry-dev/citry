import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Benchmark layout only: the runner copies this app to <env>/work/<case>/
  // and installs node_modules once in <env>. Turbopack compiles only files
  // under its root, so the root is set to <env>; left to itself it would
  // pick the repository root because of the repo's pnpm-workspace.yaml.
  turbopack: { root: path.join(__dirname, "..", "..") },
};

export default nextConfig;
