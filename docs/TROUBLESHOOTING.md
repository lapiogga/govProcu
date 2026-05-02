# 검증 단계 트러블슈팅 가이드

> SESSION-SUMMARY v3 사용자 액션 3종 + 운영 흔한 실패 케이스 모음. 우선 해당 절을 검색해서 답이 없으면 PROMPTS-LOG에 기록 후 차기 세션에서 진행.

---

## 1. Frontend (`npm install && npm run verify`)

### 1.1 npm install 실패

| 증상 | 원인 | 해결 |
|------|------|------|
| `EACCES` / 권한 오류 | npm 캐시가 관리자 권한으로 생성됨 | `npm cache clean --force` 후 재시도 |
| `ETIMEDOUT` | 사내 프록시 차단 | `npm config set registry https://registry.npmjs.org/` + 회사 프록시 설정 |
| `peer dep` 충돌 | React 19 RC 일부 패키지가 React 18 요구 | `--legacy-peer-deps` 옵션 |
| `node-gyp` Windows | Visual Studio Build Tools 부재 | `npm install --global windows-build-tools` 또는 VS Build Tools 2022 설치 |
| Node 버전 불일치 | Node 20+ 요구 | `node -v` 확인, 미만이면 nvm-windows로 LTS 설치 |

### 1.2 `npm run verify` 실패

verify는 `tsc --noEmit && next build`. 자주 깨지는 곳:

- **TS 오류 — `Type '"use cache"' ...`**: `next.config.ts` `experimental.dynamicIO: true` 누락
- **`@/components/ui/...` 모듈 못 찾음**: `tsconfig.json` `paths` 의 `@/*` 매핑 확인
- **AI SDK route 타입 오류**: `@ai-sdk/anthropic` minor 버전이 `ai@5` 와 호환되는지 확인 (`npm ls ai @ai-sdk/anthropic`)
- **xyflow build 실패**: `@xyflow/react` 가 Server Component 진입점에서 import 되면 안 됨 — 페이지에서 `'use client'` 분리 컴포넌트로 옮길 것

### 1.3 `npm run dev` 후 화면 빈 페이지

- 브라우저 콘솔에 `Hydration mismatch` → 시간 표시 등 클라이언트/서버 불일치. 해당 컴포넌트 `suppressHydrationWarning` 또는 `'use client'` 강제
- API 라우트 500 → MCP 서버 (`localhost:8080`) 미기동. `uvicorn app.server:app --port 8080` 먼저 띄우고 reload
- `ANTHROPIC_API_KEY` 미설정 → `/console` 만 깨짐. `frontend/.env.local` 추가

---

## 2. ML 학습 (`pip install -e ".[ml]"` + dataset/train/calibrate)

### 2.1 의존성 설치 실패

| 증상 | 해결 |
|------|------|
| `lightgbm` Windows 휠 없음 | Python 3.11 또는 3.12 사용. 3.13 RC 는 미지원 휠 다수 |
| `shap` 빌드 실패 | `numpy` 먼저 설치 후 재시도. `pip install --upgrade pip setuptools wheel` |
| `aiosqlite` import 오류 | extras [ml] 와 별개로 베이스 의존성 — `pip install -e .` 먼저 |

### 2.2 dataset 비어있음

```bash
python -m app.ml.dataset --days 90
# → "no rows" 또는 0 row CSV
```

원인:
- ETL 미실행 — `python scripts/etl_daily.py --days 7` 먼저 실행
- G2B API 키 미설정 — `.env`에 `G2B_BID_PUBLIC_INFO_KEY` 등 6 키 입력
- DB 파일 위치 — `runtime/govprocu.db` 가 생성됐는지 확인. 없으면 ETL 미실행 확인

### 2.3 train_v2 GridSearch 너무 오래 걸림

- 데이터 < 50 rows → `error: insufficient data` 정상 동작. dataset 더 누적 후 재시도
- 24 candidates × 5 fold = 120 fit. 1000 row 기준 5~10분 소요. 타임아웃이면 `param_grid` 격자 축소

### 2.4 calibrate 실패

- `model_award_rate.txt` 없음 → train v1 먼저 실행 (`python -m app.ml.train`)
- IsotonicRegression 동작 안 함 → 학습 데이터 분산 부족. 데이터 더 누적

---

## 3. Neo4j R&D PoC (`docker compose up -d`)

### 3.1 Docker 자체 문제

| 증상 | 해결 |
|------|------|
| `docker: command not found` | Docker Desktop 설치 (Windows: WSL2 백엔드) |
| `port 7474 already in use` | 기존 Neo4j 종료 또는 `docker-compose.yml` ports 매핑 변경 |
| `image pull rate limit` | Docker Hub 무로그인 한도 초과 — `docker login` |

### 3.2 ETL 스크립트 실패

```bash
python scripts/etl_to_neo4j.py --days 7
# → ConnectionError / AuthenticationError
```

- `NEO4J_URI` 환경변수 미설정 → `.env`에 `NEO4J_URI=bolt://localhost:7687` 추가
- 비밀번호 불일치 → `docker compose.yml` `NEO4J_AUTH=neo4j/govprocu_poc` 와 `.env` `NEO4J_PASSWORD` 동일해야 함
- driver 미설치 → `pip install -e ".[graph]"`

### 3.3 verify_neo4j_poc 쿼리 결과 0

- ETL 미완료 — `docker compose logs neo4j` 로 부팅 완료 확인 후 ETL 재실행
- GovProcu DB 자체에 데이터 없음 → 위 ML §2.2 참조

### 3.4 GDS 플러그인 미적용

- `find_collusion_clusters` 호출 시 `procedure not found: gds.louvain.stream`
- `docker-compose.full.yml` 의 `NEO4J_PLUGINS=["graph-data-science"]` 환경변수 확인
- 플러그인 다운로드는 컨테이너 첫 부팅 1~2분 소요 — `docker compose logs -f neo4j` 로 "Started." 확인 후 사용

---

## 4. MCP 서버 (`uvicorn app.server:app`)

### 4.1 import 오류

```
ModuleNotFoundError: No module named 'app.tools.graph'
```
→ `pip install -e .` 재실행 (editable install 갱신)

### 4.2 64개 도구 등록 실패

- `mcp.tool()(...)` 호출에서 함수 시그니처 검증 실패 → `app/server.py` import 시점 traceback 확인
- 새로 추가한 도구가 async가 아니면 등록 안 됨

### 4.3 인증 실패

```
401 Unauthorized
```
- `MCP_API_TOKENS=token1,token2` `.env` 미설정 → AuthMiddleware가 모든 요청 거부
- 개발 시 우회: `MCP_AUTH_DISABLED=true` (운영에서는 절대 사용 금지)
- 클라이언트 헤더 형식: `Authorization: Bearer <token>`

### 4.4 NTS quota 초과

- 일일 호출 한도 도달 → `runtime/govprocu.db` `nts_quota` 테이블 row 확인
- 강제 리셋 (개발용): `DELETE FROM nts_quota WHERE date = DATE('now');`

---

## 5. 환경변수 체크리스트

`.env` (MCP 서버):
```
G2B_BID_PUBLIC_INFO_KEY=
G2B_SCSBID_KEY=
G2B_CONTRACT_KEY=
G2B_STAT_KEY=
NTS_BIZ_STATUS_KEY=
NTS_BIZ_VERIFY_KEY=
MCP_API_TOKENS=devtoken1,devtoken2
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=govprocu_poc
SMTP_HOST=
SLACK_WEBHOOK_URL=
KAKAO_API_KEY=
LH_API_KEY=
EX_API_KEY=
KWATER_API_KEY=
KORAIL_API_KEY=
```

`frontend/.env.local`:
```
ANTHROPIC_API_KEY=
MCP_BASE_URL=http://localhost:8080
MCP_API_TOKEN=devtoken1
```

---

## 6. 막혔을 때

1. 에러 메시지 + 명령 + OS 버전 → `logs/TERMINAL-LOG.md` 에 timestamp 와 함께 기록
2. PROMPTS-LOG에 "(증상) 디버깅" 발화로 추가
3. 차기 세션에서 본 문서 검색 → 없으면 추가

작성: 2026-05-02 · 검증 단계 사용자 액션 3종 + 운영 흔한 실패 모음
