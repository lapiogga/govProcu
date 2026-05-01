import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // GovProcu 데스크톱·태블릿 웹앱 (모바일 비대상)
  output: "standalone",  // NEXT5-5 Docker 배포 (Dockerfile.frontend)
  experimental: {
    // NEXT4-2: Cache Components 활성화 (Next.js 15+)
    // FRONTEND-TECH.md Wave 2 — analytics/agencies 캐시 적중 시 ms 응답
    cacheComponents: true,
  },
  env: {
    GOVPROCU_MCP_URL:
      process.env.GOVPROCU_MCP_URL || "http://localhost:8080",
  },
};

export default nextConfig;
