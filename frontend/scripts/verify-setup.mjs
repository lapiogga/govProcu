#!/usr/bin/env node
/**
 * GovProcu Frontend 검증 스크립트.
 * 사용자 5/2 24번 [NEXT-4]. npm install 후 실행.
 *
 * 검증 항목:
 * 1. node_modules 존재
 * 2. 핵심 의존성 (next, react, ai SDK, tailwindcss) 설치 확인
 * 3. tsconfig.json 유효성 (tsc --noEmit)
 * 4. 환경변수 (ANTHROPIC_API_KEY, GOVPROCU_MCP_URL)
 * 5. MCP 서버 연결 (선택)
 *
 * 사용:
 *   cd frontend
 *   npm install
 *   node scripts/verify-setup.mjs
 */
import { existsSync, readFileSync } from "node:fs";
import { execSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(__dirname, "..");

let pass = 0;
let fail = 0;
let warn = 0;

function ok(msg) {
  console.log(`OK  ${msg}`);
  pass++;
}
function bad(msg) {
  console.log(`FAIL  ${msg}`);
  fail++;
}
function warning(msg) {
  console.log(`WARN  ${msg}`);
  warn++;
}

console.log("=".repeat(60));
console.log("GovProcu Frontend 검증");
console.log("=".repeat(60));

// 1. node_modules
const nodeModules = resolve(frontendRoot, "node_modules");
if (existsSync(nodeModules)) {
  ok("node_modules 존재");
} else {
  bad("node_modules 없음 → npm install 실행 필요");
  process.exit(1);
}

// 2. 핵심 의존성
const required = [
  "next",
  "react",
  "react-dom",
  "ai",
  "@ai-sdk/anthropic",
  "@ai-sdk/react",
  "tailwindcss",
  "typescript",
];
for (const pkg of required) {
  const pkgPath = resolve(nodeModules, pkg, "package.json");
  if (existsSync(pkgPath)) {
    const v = JSON.parse(readFileSync(pkgPath, "utf-8")).version;
    ok(`${pkg}@${v}`);
  } else {
    bad(`${pkg} 미설치`);
  }
}

// 3. tsconfig 검증
try {
  execSync("npx tsc --noEmit --pretty", {
    cwd: frontendRoot,
    stdio: "pipe",
  });
  ok("tsc --noEmit (타입 검증)");
} catch (err) {
  const out = err.stdout?.toString() || err.stderr?.toString() || "";
  bad(`tsc 오류:\n${out.slice(0, 500)}`);
}

// 4. 환경변수
const envLocal = resolve(frontendRoot, ".env.local");
if (existsSync(envLocal)) {
  const content = readFileSync(envLocal, "utf-8");
  if (/ANTHROPIC_API_KEY=\S+/.test(content)) {
    ok("ANTHROPIC_API_KEY 설정됨");
  } else {
    warning("ANTHROPIC_API_KEY 미설정 (자연어 콘솔 사용 시 필수)");
  }
  const mcpMatch = content.match(/GOVPROCU_MCP_URL=(\S+)/);
  if (mcpMatch) {
    ok(`GOVPROCU_MCP_URL = ${mcpMatch[1]}`);
  } else {
    warning("GOVPROCU_MCP_URL 미설정 (기본값 http://localhost:8080 사용)");
  }
} else {
  warning(".env.local 없음 → cp .env.example .env.local 후 키 입력");
}

// 5. MCP 서버 ping (선택)
const mcpUrl = process.env.GOVPROCU_MCP_URL || "http://localhost:8080";
try {
  const resp = await fetch(`${mcpUrl}/`, { method: "GET" });
  if (resp.ok || resp.status === 405 || resp.status === 404) {
    ok(`MCP 서버 응답 (${mcpUrl} → HTTP ${resp.status})`);
  } else {
    warning(`MCP 서버 비정상 응답 (HTTP ${resp.status})`);
  }
} catch (err) {
  warning(
    `MCP 서버 연결 실패 (${mcpUrl}). uvicorn app.server:app --port 8080 가동 권장`,
  );
}

console.log("=".repeat(60));
console.log(`결과: ${pass} PASS / ${fail} FAIL / ${warn} WARN`);
console.log("=".repeat(60));

if (fail > 0) {
  process.exit(1);
}

console.log("\nOK 다음 단계:");
console.log("  npm run dev");
console.log("  http://localhost:3000");
console.log("  /console — AI 자연어 콘솔");
console.log("  /bids/trace?no=20240315678 — 입찰 상세 추적");
