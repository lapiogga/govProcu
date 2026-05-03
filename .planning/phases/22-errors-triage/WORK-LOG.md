# Phase 22 — WORK-LOG (시계열)

> 본 phase에서 수행된 모든 작업을 시간 순서로 기록. PROMPTS-LOG (사용자 input)과 분리.

## 2026-05-03 (일)

| 시각 (KST) | 행위자 | 작업 | 결과 / 산출물 |
|-----------|--------|------|---------------|
| 20:43 | lead | err-01~05.png 5장 시각 분석 | 결함 사실 5건 도출 (F1~F5) |
| 20:43 | lead | grep 8080/8081 + trace_bid_lifecycle | F1 포트 미스매치 즉시 확정 (frontend 8081, backend 8080) |
| 20:44 | lead | 인프라 생성 | `.planning/PROMPTS-LOG.md` 신규, `.planning/phases/22-errors-triage/{PLAN,WORK-LOG}.md` 신규 |
| 20:45 | lead | TaskCreate #1~#6 + 자율 v21 (74501a8) commit msg 분석 | F1 fix 방향 정정: 8080→8081 통일 (v21 의도 보존). PLAN.md Step A 갱신 |
| 20:46 | lead | F1 코드 정합 6 파일 수정 | `app/config.py:45` 8081 / `app/server.py:4` docstring / `.env.example:57` / `frontend/.env.example:7-8` / `frontend/src/app/page.tsx:43` footer. (frontend/next.config.ts, mcp-client.ts는 v21에서 처리됨) |
| 20:46 | lead | 환경 점검 | 사용자 `.env` SERVER_PORT=8080 (수정 필요), 포트 8080에 외부 PID 7948+37424 LISTEN, 8081 free → 8081 통일 결정 정당 |
| 20:47 | lead | sub-agent 3개 병렬 spawn (Explore, F2/F3/F4+F5) | 코드 read-only 진단 시작 |
| 20:50 | Agent A (F2) | 진단 보고 도착 | **P1(85%): v15.1 30일 폴백 trade-off**. P2(60%): inqryDiv=1 예외 삼킴. P3(40%): bid_no 정규화. 수정안: progressive + R 형식 연도 범위. |
| 20:52 | Agent B (F3) | 진단 보고 도착 | **P1(80%): `award.py:270` 부분일치 매칭 — 변형 표기와 미매칭**. P2(15%): award_rate NULL. P3(5%): 5년/52chunk timeout. 수정안: 정확 매칭 + 유사도 + 표기 학습 메시지. |
| 20:52 | Agent C (F4·F5) | 진단 보고 도착 | **F4 P1(75%): `bid.py:211-215` has_more 단순 비교**. F5 **P1(70%): v21 fix가 이미 해결한 가능성** (8080 외부 서버 500). 수정안: F4=빈 matches 시 has_more=False. F5=사용자 환경 재현 우선. |
| 20:55 | lead | ROOT-CAUSE.md 통합 갱신 | F1~F5 5건 root cause 정리. 종합 fix 순서 확정: v22.1(F1 commit) → v22.2(F4 has_more) → v22.3(F2 progressive) → v22.4(F3 별도 phase) → v22.5(chore) → v22.6(F5 검증) |
| 20:58 | lead | v22.1 atomic commit (db7fb41) | F1 코드 5 파일 + .planning 메타 4 파일. logs/WORK-LOG.md(외부 sync hook 자동 추가)는 제외 |
| 21:00 | lead | v22.2 F4 fix 적용 | `app/tools/bid.py:215+` `if not matches: has_more = False` 보수적 정정. 빈 매칭 시 다음 페이지 권유 차단 → 사용자 모순 메시지 ("결과 없음 (25966건). 다음 페이지를 시도하세요") 제거 |
| 21:02 | lead | v22.2 commit (9729f72) | atomic — bid.py + WORK-LOG |
| 21:05 | lead | v22.3 F2 fix 적용 | `app/tools/bid.py` 모듈 상단 `structlog` import + `log` 글로벌. `get_bid_notice_detail` 3차 폴백을 R/숫자 형식이면 `_infer_period_from_bid_no` 연도 범위 1회 시도, 형식 불명이면 30→90일 progressive로 변경. `except Exception: pass` → `log.warning(...) + continue`로 가시화. `fallback_range` 필드 추가로 어느 범위에서 매칭됐는지 응답 동봉. import sanity check OK |
