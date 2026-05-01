# GovProcu 운영 가이드 (OPERATIONS)

> 작성: 2026-05-02
> 일일 점검 + 장애 대응 + 사용자 관리

---

## 1. 일일 점검 (5분)

### 매일 09:00 KST
```bash
# 1. ETL 상태
python -c "import asyncio; from app.storage.etl_state import list_jobs; \
    print(asyncio.run(list_jobs()))"

# 2. SQLite 크기 + 백업
ls -lh runtime/govprocu.db
ls -lh backup/

# 3. MCP 서버 헬스체크
curl -s http://localhost:8080/  # 응답 확인

# 4. 자동 push 결과 (git log)
git log --oneline -3
```

체크리스트:
- [ ] ETL `daily_award_etl` last_synced_at 24시간 이내
- [ ] SQLite 크기 정상 범위
- [ ] backup/ 최신 파일 어제 03:30 이후
- [ ] MCP HTTP 응답 정상
- [ ] origin/main과 mount 동기화

---

## 2. 사용자 토큰 관리

### 2.1 발급
`.env` 의 `MCP_API_TOKENS` 에 콤마로 구분:
```env
MCP_API_TOKENS=alice-2026Q2-xxx,bob-2026Q2-yyy
```

### 2.2 사용자별 데이터 격리
- SQLite `subscriptions.user_token` / `watchlist.user_token` / `digest_log.user_token`
- 모든 알림·즐겨찾기는 토큰 단위로 분리됨

### 2.3 회수
1. `.env` 에서 토큰 제거 → 서버 재시작
2. SQL 정리 (선택):
   ```sql
   UPDATE subscriptions SET active=0 WHERE user_token=?;
   DELETE FROM watchlist WHERE user_token=?;
   ```

---

## 3. 장애 대응 시나리오

### 3.1 G2B API 403 / 401
**증상**: search_bid_notices 등 G2B 도구 일제히 실패.
**원인**:
- 키 만료 또는 IP 화이트리스트 변경
- data.go.kr 점검

**조치**:
1. data.go.kr 활용신청 페이지에서 만료일 확인
2. 운영 IP 변경 여부 (방화벽/nginx 로그)
3. 백오프 후 재시도 — tenacity가 자동 처리

### 3.2 NTS 한도 초과
**증상**: check_business_status 일일 한도 도달.
**조치**:
- 일일 한도 100건 (사업자 등록정보 진위확인 API 표준)
- 한도 늘리려면 활용신청 추가 또는 Redis 캐시 TTL 24h+ 적용

### 3.3 SQLite Lock
**증상**: 다중 worker에서 `database is locked`.
**조치**:
- `journal_mode=WAL` 활성 확인 (aiosqlite 기본 자동 X — 설정 추가 필요 시)
- worker 수 1로 임시 축소
- 장기 해결: PostgreSQL 마이그레이션 검토

### 3.4 자연어 콘솔 LLM 오류
**증상**: /console 에서 응답 없음 또는 401.
**원인**:
- ANTHROPIC_API_KEY 만료/한도
- Claude 모델명 변경

**조치**:
1. console.anthropic.com 에서 키 + usage 확인
2. `frontend/src/app/api/chat/route.ts` 에서 model 이름 최신 (claude-sonnet-4-6 등)
3. Anthropic 상태 페이지 확인

### 3.5 Frontend 빌드 실패
**증상**: `npm run build` 에서 type 오류.
**조치**:
1. `npm run verify` (verify-setup.mjs) 로 deps 재확인
2. `npm ci` (lockfile 기준 재설치)
3. `tsc --noEmit` 출력에서 첫 오류 우선 수정

---

## 4. 정기 작업

### 매주 월요일 09:00
- [ ] backup/ 7일 이전 파일 정리
- [ ] ML 모델 재학습 (`python -m app.ml.dataset --days 90 && python -m app.ml.train`)
- [ ] 캘리브레이션 검증 (`python -m app.ml.calibrate`)
  - MAE > 5%p 또는 MACE > 5%p 시 feature 보강 검토

### 매월 1일
- [ ] G2B 키 호출수 통계 (data.go.kr 마이페이지)
- [ ] WORK-LOG / TERMINAL-LOG 1개월 이상 행 archive
- [ ] PROMPTS-LOG 분기별 백업

### 분기별
- [ ] SQLite VACUUM (크기 압축):
  ```bash
  sqlite3 runtime/govprocu.db "VACUUM;"
  ```
- [ ] dependency 업데이트 (`pip list --outdated`, `npm outdated`)
- [ ] 접근 토큰 갱신 (PAT, MCP_API_TOKENS)

---

## 5. 사용자 지원 FAQ

### Q1. "공고번호 추적했는데 5단계가 미완료"
- 사전규격은 일부 공고만 등록됨 (공사 위주). 미등록 = 정상.
- NTS 검증은 낙찰자 사업자번호가 응답에 있을 때만 작동.

### Q2. "투찰가 예측이 정확하지 않다"
- v0 휴리스틱: 발주기관 낙찰률 분위수 룩업.
- v1 ML: 90일 학습 데이터로 LightGBM. dataset 보강 시 정확도 향상.
- 사정률 패턴이 표준편차 5%p 초과면 경고 표시.

### Q3. "다중 발주기관 검색이 G2B만 보임"
- LH/도로공사/수자원/코레일 어댑터는 PENDING_KEY 상태.
- data.go.kr 에서 해당 기관 OpenAPI 활용신청 후 환경변수 추가:
  ```env
  LH_API_KEY=...
  EX_API_KEY=...
  KWATER_API_KEY=...
  KORAIL_API_KEY=...
  ```
- 어댑터 STATUS 를 ACTIVE 로 변경 (`app/clients/external/lh.py` 등) + 본문 구현.

### Q4. "그래프DB 화면이 없다"
- Neo4j는 R&D 단계. R1 PoC 검증 통과 후 R3에서 MCP 도구 통합 + UI 추가.

---

## 6. 인시던트 보고 양식

```markdown
## YYYY-MM-DD 인시던트 — <간단 요약>

**시작**: HH:MM KST
**감지**: <어떻게 감지>
**영향**: <영향 받은 사용자/기능>
**원인**: <근본 원인>
**조치**: <시간순 조치 내역>
**복구**: HH:MM KST
**재발 방지**:
- [ ] <action item 1>
- [ ] <action item 2>
```

→ logs/ 또는 별도 INCIDENTS.md 에 누적.

---

## 7. 연락처

- GitHub: lapiogga/govProcu
- 이슈: GitHub Issues
- 긴급: PROMPTS-LOG 마지막 사용자 발화 기준 우선순위 확인
