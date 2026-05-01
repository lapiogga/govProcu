import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // GovProcu 데스크톱·태블릿 웹앱 (모바일 비대상)
  experimental: {
    // Cache Components — Next.js 15 신기능 (FRONTEND-TECH.md Wave 2)
    // 운영 안정성 검증 후 활성화: cacheComponents: true,
  },
  // MCP 서버 호출은 서버 액션 또는 route handler에서
  env: {
    GOVPROCU_MCP_URL:
      process.env.GOVPROCU_MCP_URL || "http://localhost:8080",
  },
};

export default nextConfig;
