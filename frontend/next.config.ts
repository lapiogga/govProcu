import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // GovProcu 데스크톱·태블릿 웹앱 (모바일 비대상)
  output: "standalone", // NEXT5-5 Docker 배포 (Dockerfile.frontend)
  // NEXT7-SEC-1: Next 15.5.15 stable에서 cacheComponents 는 canary-only.
  // 'use cache' directive + cacheTag 는 임시 비활성. Next 16 정식 출시 후 재활성 (R&D 트랙).
  env: {
    GOVPROCU_MCP_URL: process.env.GOVPROCU_MCP_URL || "http://localhost:8080",
  },
};

export default nextConfig;
