# Phase 25 — 운영 8081 정합 chore (port-ops-chore)

> **이전 phase**: 24-vendor-matching (v24.1~v24.4 완료)
> **시작**: 2026-05-03 23:15 KST
> **목표**: Phase 22 v22.7에서 보류한 docker-compose / e2e.yml + Dockerfile EXPOSE 정합

## 1. 보류 사유 (Phase 22)

- Dockerfile EXPOSE 8080 + CMD --port 8080 하드코딩
- docker-compose ports `"8080:8080"` (host:container)
- e2e.yml `GOVPROCU_MCP_URL=http://localhost:8080`

Dockerfile 변경 없이 docker-compose만 8081로 바꾸면 컨테이너 내부 8080 LISTEN ↔ 외부 매핑 불일치 → 운영 깨짐. 일괄 변경 필요.

## 2. v25.1 변경 대상 (4 파일, 8 라인)

| 파일 | 변경 |
|------|------|
| `deploy/Dockerfile` | EXPOSE 8081 / HEALTHCHECK :8081 / CMD --port 8081 |
| `deploy/docker-compose.yml` | ports `"8081:8081"` |
| `deploy/docker-compose.full.yml` | header 주석 / ports / GOVPROCU_MCP_URL=http://mcp:8081 |
| `.github/workflows/e2e.yml` | env GOVPROCU_MCP_URL=http://localhost:8081 |

## 3. 검증

- `grep -rn 8080` 결과: historical record(.planning, SESSION-SUMMARY, logs)만 잔존 — OK
- Dockerfile + docker-compose 정합 확인
- CI workflow는 실제 backend 안 띄우므로 dummy URL이라 실 효과 없으나 일관성

## 4. 후속 (별도)

- 사용자 .env에 SERVER_PORT=8080 잔존 시 8081로 변경 안내 (Phase 22 v22.1에서 이미 안내)
