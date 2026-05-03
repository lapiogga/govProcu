# Phase 22 — errors-triage (자율 v22)

> **목표**: 사용자 제공 err-01~05.png 5장의 결함을 **분류·근원 진단·수정·검증**까지 GSD 사이클로 완료.
> **시작**: 2026-05-03 20:43 KST
> **방법론**: get-shit-done + Team Agent 분담 + sub Agent 병렬 분석 + 시계열 기록

## 1. 결함 사실표 (5건)

| ID | 화면 | 증상 | 1차 추정 |
|----|------|------|----------|
| **F1** | localhost:8081 | ERR_CONNECTION_REFUSED (사이트 연결 불가) | **포트 미스매치 확정** — frontend 기본 8081 vs backend 기본 8080 (자율 v21에서 frontend만 변경) |
| **F2** | 입찰 추적 R26BK01435763-000 | `trace_bid_lifecycle` 호출 후 모든 필드 "—", 응찰자수 0, 단계별 ○ 미완료 | MCP 단건조회 결과 비정상 또는 채번 매칭 실패 |
| **F3** | 발주기관 분석 (경찰청 경찰대학, 2020-01-01 ~ 2026-05-01) | "사정률 패턴: 데이터 없음 (낙찰률 데이터 없음)" | 발주기관명 매칭/조인 로직 또는 ETL 데이터 부재 |
| **F4** | 입찰 검색 (해군 정보체계, 용역, 2026-03-01~04-01, 페이지 2) | "결과 없음 (25966건). 페이지 2." | 총 25966건 ↔ 페이지 2 빈 결과: 페이징(cursor) 또는 검색 결과 표시 버그 |
| **F5** | 입찰 검색 (구축사업, 용역, 2026-03-01~03-20, 깊은 검색 5x LIKE) | "오류: HTTP 500" | 백엔드 deep search 분기에서 예외 발생 |

## 2. 우선순위 (블로커 우선)

```
F1 (P0, infra) ──▶ 다른 모든 결함 검증 차단 (서버 연결 불가)
                                ▼
                        F2 (P1, mcp) — 단건조회 핵심 기능
                                ▼
                        F5 (P1, backend) — HTTP 500 (deep)
                                ▼
                        F4 (P2, backend) — 페이징
                                ▼
                        F3 (P2, backend) — 발주기관 분석 데이터
```

## 3. 팀 구성 (TeamCreate: errors-triage-v22)

| 팀 | 담당 | 모델 | 작업 |
|----|------|------|------|
| **lead** (오케스트레이터, 본인) | 통합 의사결정·진행 추적·시계열 기록 | opus | 팀 분담, F1 직접 수정, 결과 종합, 커밋 |
| **infra-team** | F1 (포트 통일) | sub: gsd-executor (sonnet) | 8080/8081 전수 조사 → 통일 결정 → 일괄 수정 |
| **mcp-team** | F2 (trace_bid_lifecycle) | sub: Explore + gsd-debugger (opus) | tools/workflow.py 진단, 채번 R26BK01435763-000 실데이터 폴백 흐름 분석 |
| **backend-team** | F3·F4·F5 (백엔드 3종) | sub: Explore + gsd-debugger (opus) | search/agencies endpoint, deep_search 분기, 페이징 cursor 진단 |

> **상호 의사결정 채널**: F1 fix가 8080으로 통일이냐 8081로 통일이냐는 backend-team과 lead가 협의 후 결정. mcp-team은 그 결정 후 분석 실행 가능.

## 4. 진행 단계

### Step A — 환경 정상화 (F1) [lead + infra-team]
1. 8080/8081 사용처 전수 grep
2. **결정 정정 (자율 v21 의도 보존)**: 운영 표준 **8081로 통일**.
   - 근거: v21 커밋 메시지에 "8080 충돌 회피, 운영 표준 8081" 명시. 현재 8080에 외부 프로세스 PID 7948 + 37424 LISTEN 중 (`Get-NetTCPConnection`). 8081은 free.
   - frontend(next.config.ts, mcp-client.ts)는 v21에서 이미 8081로 변경. backend 측만 정합 필요.
3. 핵심 6 파일 수정: `app/config.py` · `app/server.py` docstring · `.env.example` · `frontend/.env.example` · `frontend/src/app/page.tsx` footer (6번째는 v21에서 처리됨)
4. 사용자 액션: 로컬 `.env`의 `SERVER_PORT=8080` → 삭제(권장) 또는 `8081`로 변경
5. 서버 8081 재기동 → 화면 확인
6. atomic commit (v22.1)
7. **후속 chore (v22.2)**: docs/ (README/DEPLOY/USER-GUIDE/TROUBLESHOOTING/OPERATIONS) + docker-compose 2종 + e2e.yml 정합 — F2~F5 진단 완료 후 묶음 커밋

### Step B — 병렬 진단 (F2/F3/F4/F5) [팀 분담]
- mcp-team: F2 진단 → 보고 (ROOT-CAUSE.md)
- backend-team: F3·F4·F5 진단 → 보고 (ROOT-CAUSE.md)

### Step C — 통합 검토 + 수정안 우선순위 [lead]
- 4건 보고 병합, 중복/연쇄 의존 식별
- 사용자 검증 가능한 단위로 분할

### Step D — 수정 + 검증 [팀 분담, atomic 커밋]
- 각 fix별 단위 테스트 + 화면 검증 가이드 작성
- 커밋 메시지 양식: `fix(...) — 자율 v22.N`

### Step E — UAT 핸드오프 [lead]
- UAT.md 결함 매핑 + 사용자 재현 가이드
- PROMPTS-LOG / WORK-LOG 정합성 점검

## 5. 컨텍스트 관리

- 80% 도달 시: WORK-LOG.md에 체크포인트 → `/compact`
- sub-agent 결과는 ROOT-CAUSE.md에 요약 (raw 컨텍스트 영구화 금지)
- TaskCreate로 6단계 진행 추적 (Step A~E + 커밋)

## 6. 성공 기준

- [ ] F1: localhost 정상 접속 (포트 통일)
- [ ] F2: trace_bid_lifecycle 정상 결과 또는 폴백 사유 명시
- [ ] F3: 발주기관 분석 데이터 표시 또는 "데이터 없음 정당성" 검증 (etl 상태 점검)
- [ ] F4: 페이징 진위 확정 + UI 일치
- [ ] F5: 깊은 검색 HTTP 500 제거
- [ ] 모든 fix atomic 커밋 + UAT.md 갱신 + PROMPTS-LOG 시계열 정합
