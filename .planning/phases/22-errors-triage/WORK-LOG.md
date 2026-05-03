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
| 21:08 | lead | v22.3 commit (b71f4d2) | atomic |
| 21:18 | user | 화면 검증 결과 보고 (발화 #4) | 신규 결함 3건 (F6/F7/F8) 보고. F1 포트 fix 효과 OK (다른 화면 작동), F2 trace 작동하나 느림, F3 발주기관 작동하나 느림, F7 업체 프로필 빈 화면, F8 입찰검색 매칭 실패 |
| 21:20 | lead | sub-agent 2개 spawn (F7, F8 진단) + UX fix(F6) 코드 분석 병렬 | TaskCreate #7~9 |
| 21:25 | lead | F6 코드 적용 (UX) | `bids/trace/page.tsx` TimelineSkeleton + `agencies/page.tsx` Skel + Suspense fallback label에 cursor-wait + spinner + 진행 메시지 추가 |
| 21:30 | user | 발화 #5 "전체적으로 조회하는 속도가 많이 느림" | F9 신규 결함 (성능). Phase 23 신설 권장 |
| 21:32 | Agent F8 | 진단 보고 도착 | **HIGH**: G2B keyword 파라미터 미지원 → 클라이언트 999건 필터. **HIGH**: v22.2 fix 부작용 (정상 케이스에서도 has_more=False 차단). MEDIUM: 30일 default 너무 좁음. → v22.6 정정안 |
| 21:32 | Agent F7 | 진단 보고 도착 | **1순위(90%)**: V1~V3 도구 스텁 + NTS 키 미설정으로 backend가 빈 sections 응답. frontend 조건부 렌더링이 모두 스킵 → 빈 화면 인식. → v22.5 frontend 명시 안내 fix |
| 21:34 | lead | ROOT-CAUSE.md F6/F7/F8/F9 섹션 신규 + 종합 fix 순서 갱신 | v22.4 (F6 commit 대기) → v22.5 (F7) → v22.6 (F8) → v22.7 (chore) → Phase 23 (F9) → Phase X (F3, F5) |
| 21:38 | user | 발화 #6 "5초 이내 SLA" | F9에 5초 SLA 명시. Phase 23 design proposal 재정의 (Streaming 1st-byte + default 기간 대폭 단축 + R 폴백 lighter + 호출 병렬화 + 사전 ETL cache) |
| 21:42 | lead | v22.4 commit (e66f1b7) | atomic — frontend UX 2 파일 + ROOT-CAUSE/WORK-LOG/PROMPTS-LOG |
| 21:50 | user | 발화 #7 "1" | 옵션 1 선택 — Phase 22 잔여 마무리 후 Phase 23 가동 |
| 21:52 | lead | v22.5 F7 fix 적용 | `frontend/src/app/vendors/[bizNo]/page.tsx`: data null 분기 강화 (응답 파싱 실패 명시). `hasAnyData` 검증 + 빈 응답 시 명시 안내 panel (가능 원인 4종 + implementation_status). NTS 섹션에 키 미설정 안내. backend는 변경 없음 — frontend 분기만 강화 |
| 21:55 | lead | v22.5 commit (e2762d7) | atomic — vendors/[bizNo]/page.tsx + WORK-LOG + PROMPTS-LOG |
| 22:00 | lead | v22.6 F8 fix 적용 | (1) `app/tools/bid.py:215+` `if not matches: has_more = False` (v22.2) → `if scanned_total == 0: has_more = False` 정정. G2B 데이터 받았으나 keyword/inst 필터로 매칭 0건이면 다음 페이지에 매칭 가능성 → has_more 유지 (사용자 검색 차단 해제). (2) `frontend/src/app/bids/page.tsx`: `params.keyword?.trim()` 추가 + `trimmedInst` 동시 분기 + 메시지에 inst_name 동시 표시. import sanity check OK |
