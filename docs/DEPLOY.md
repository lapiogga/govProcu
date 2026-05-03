# GovProcu 배포 가이드 (DEPLOY)

> 작성: 2026-05-02
> 대상: 사내·조직 전용 단일 인스턴스 배포 (데스크톱 웹앱 + MCP 서버)

---

## 1. 시스템 구성

```
[브라우저]  ──HTTPS──▶  [Next.js frontend (3000)]
                                 │
                                 ▼  Server Actions
                       [GovProcu MCP (8081)]
                          ├─▶ G2B OpenAPI (apis.data.go.kr)
                          ├─▶ NTS OpenAPI (api.odcloud.kr)
                          ├─▶ SQLite (govprocu.db)  ← 알림·즐겨찾기·ETL state
                          ├─▶ Redis (선택, 캐시·rate limit)
                          └─▶ Neo4j (선택, R&D 그래프DB)
```

**필수**: MCP 서버 + frontend
**선택**: Redis (캐시), Neo4j (그래프 R&D)

---

## 2. 사전 준비

### 2.1 API 키
- `.env` 작성 (template: `.env.example`):
  ```env
  G2B_KEY_BID=...        # 입찰공고
  G2B_KEY_PRESPEC=...    # 사전규격
  G2B_KEY_AWARD=...      # 낙찰
  G2B_KEY_CONTRACT=...   # 계약과정통합공개
  G2B_KEY_USER=...       # 사용자정보
  G2B_KEY_STATS=...      # 통계
  NTS_API_KEY=...        # 사업자 진위확인
  MCP_API_TOKENS=token1,token2  # 사용자 Bearer
  REDIS_URL=redis://redis:6379/0
  LOG_LEVEL=INFO
  SERVER_HOST=0.0.0.0
  SERVER_PORT=8081
  ```

### 2.2 frontend `.env.local`
```env
ANTHROPIC_API_KEY=sk-ant-...
GOVPROCU_MCP_URL=http://localhost:8081
```

---

## 3. 단일 호스트 배포 (Windows)

### 3.1 MCP 서버
```powershell
cd C:\Users\User\GovProcu
pip install -e .
uvicorn app.server:app --host 0.0.0.0 --port 8081 --workers 2
```

### 3.2 Frontend
```powershell
cd frontend
npm install
npm run build
npm run start    # 또는 PM2/forever로 daemon
```

### 3.3 일일 ETL (Task Scheduler)
```powershell
.\deploy\scheduler\setup-windows-task.ps1   # 관리자 권한
```

---

## 4. Docker Compose 배포 (권장)

```bash
cd deploy
docker compose up -d
```

`deploy/docker-compose.yml`이 이미 존재 (MCP + Redis). 추가:
- Neo4j R&D: `cd deploy/neo4j-poc && docker compose up -d`
- frontend는 별도 (Vercel 또는 자체 호스팅)

---

## 5. 환경별 설정

| 환경 | 차이 | 주의 |
|------|------|------|
| 개발 | uvicorn --reload, 단일 worker | .env 로컬 |
| 스테이징 | gunicorn 4 worker | Redis 필수 |
| 운영 | gunicorn + nginx + HTTPS | 백업·모니터링 필수 |

---

## 6. 백업

### 6.1 SQLite (govprocu.db)
- 사용자 알림·즐겨찾기 영속 데이터
- 매일 03:30 (ETL 후) 자동 백업 권장
```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmm"
Copy-Item runtime\govprocu.db "backup\govprocu_$ts.db"
```

### 6.2 ML 모델
- `runtime/ml/model_award_rate.txt` + `dataset_*.csv`
- 주 1회 백업 + 모델 메타 (`model_meta.json`) 보존

### 6.3 Neo4j (R&D)
- `docker compose down` 후 volume 백업

---

## 7. 모니터링 (최소)

| 항목 | 도구 | 임계 |
|------|------|------|
| MCP 응답시간 | uvicorn 로그 + structlog | p95 > 2s 알림 |
| G2B API 실패율 | tenacity 재시도 카운터 | > 5% 알림 |
| NTS 한도 | 일일 호출수 추적 | 80% 도달 알림 |
| ETL 실패 | etl_state 테이블 last_error | 2회 연속 실패 알림 |
| SQLite 크기 | du runtime/govprocu.db | > 500MB 알림 |

---

## 8. 보안 체크리스트

- [ ] `.env`는 `.gitignore` 처리됨 (확인 완료)
- [ ] PAT는 `.pat` 파일로만 보관, 권한 600
- [ ] MCP_API_TOKENS은 사용자별 분리 발급
- [ ] HTTPS 종단 (nginx + Let's Encrypt)
- [ ] CORS는 frontend origin만 허용
- [ ] NTS 키는 IP 화이트리스트 (운영 IP)
- [ ] G2B 키는 운영 IP에서만 호출 (샌드박스 차단 확인)

---

## 9. 키 갱신 주기

| 키 | 갱신 주기 | 절차 |
|----|---------|------|
| G2B 6종 | 2년 | data.go.kr 자동 연장 |
| NTS | 무기한 | 활용신청 유지 |
| GitHub PAT | 90일 | `.pat` 갱신 + push 테스트 |
| ANTHROPIC_API_KEY | 무기한 | console.anthropic.com |

---

## 10. 롤백

문제 발생 시:
```bash
git log --oneline -10
git revert <commit-id>  # 또는 reset --hard <previous>
git push origin main
```

frontend는 이전 빌드로 재배포:
```bash
cd frontend
npm ci
npm run build
pm2 restart govprocu-frontend
```
