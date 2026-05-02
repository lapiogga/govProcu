# 사용자 액션 가이드 (자율 모드 외부 의존 영역)

> 작성: 2026-05-02 (자율 v3 라운드)
> 본 문서는 **AI 오케스트레이터(Claude Code)가 자동 처리할 수 없는 외부 계정/키 발급 작업**을 한 곳에 정리한다.
> 모든 트랙은 사용자가 직접 신청·등록·승인 절차를 거쳐야 하며, 발급 후 `.env` 갱신 + 서버 재시작으로 즉시 ACTIVE 전환된다.
>
> 시점관리 v6 기준 — 모든 항목은 "외부 의존" 카테고리이며, 기능 구현은 모두 완료되어 키 발급만 남은 상태.

---

## 1. 외부 OpenAPI 키 발급 (4종) — `runtime/intel/external_apis.json` STATUS=PENDING → ACTIVE

### 1.1 LH 한국토지주택공사 분양·임대 정보

| 항목 | 내용 |
|------|------|
| 발급처 | https://apis.data.go.kr/B552031 (공공데이터포털) |
| 신청 명 | "LH주택공사_분양정보 / 임대정보" |
| 처리 시간 | 자동 승인 (즉시) |
| `.env` 키 | `LH_API_KEY` |

**단계**:
1. https://www.data.go.kr 로그인 (회원가입 시 본인인증 필요)
2. "분양정보" 또는 "임대정보" 검색 → "활용신청"
3. 마이페이지 → 인증키 (`Encoded` / `Decoded` 두 형태) 복사
4. `.env` 추가: `LH_API_KEY=<Decoded 값>`
5. 서버 재시작: `python -m app.server`
6. 검증: `python -m app.clients.external.lh --probe` (또는 dashboard `/external` 페이지)

### 1.2 EX 한국도로공사

| 항목 | 내용 |
|------|------|
| 발급처 | https://data.ex.co.kr 또는 공공데이터포털 |
| 신청 명 | "한국도로공사_사업관리 / 휴게소정보" |
| 처리 시간 | 자동 또는 영업일 1~2일 |
| `.env` 키 | `EX_API_KEY` |

LH와 동일 패턴.

### 1.3 KWater 한국수자원공사

| 항목 | 내용 |
|------|------|
| 발급처 | 공공데이터포털 |
| 신청 명 | "한국수자원공사_상수원 / 댐수문" 등 |
| 처리 시간 | 자동 승인 |
| `.env` 키 | `KWATER_API_KEY` |

### 1.4 Korail 한국철도공사

| 항목 | 내용 |
|------|------|
| 발급처 | 공공데이터포털 |
| 신청 명 | "한국철도공사_열차편성 / 운행정보" |
| 처리 시간 | 자동 승인 |
| `.env` 키 | `KORAIL_API_KEY` |

발급 후 일괄 갱신:
```bash
# .env 수정 후
runtime/intel/external_apis.json 의 status 필드 PENDING → ACTIVE 자동 전환은 없음.
직접 갱신 또는 다음 ETL 사이클에서 자동 검증 후 전환되도록 설계되어 있음 (etl_daily.py).
```

---

## 2. 알림 채널 (3종) — 발송 인프라

### 2.1 SMTP (이메일)

선택지 (`docs/NOTIFICATIONS.md` §1):

| 옵션 | 비용 | 신청 |
|------|------|------|
| Gmail SMTP | 무료 (500/일) | Google 계정 + App Password 생성 |
| AWS SES | $0.10/1k | aws.amazon.com → SES 콘솔 |
| SendGrid | 무료 100/일 | sendgrid.com 가입 |
| Mailgun | 무료 5k/월 | mailgun.com 가입 |

**Gmail App Password 단계**:
1. https://myaccount.google.com/apppasswords
2. 2단계 인증 활성화 (필수 선결 조건)
3. App Password 생성 → 16자리 복사
4. `.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=<your_email>@gmail.com
   SMTP_PASS=<16자리 App Password>
   SMTP_FROM=GovProcu <noreply@your-domain>
   ```

### 2.2 Slack Incoming Webhook

| 항목 | 내용 |
|------|------|
| 발급처 | https://api.slack.com/messaging/webhooks |
| 채널 권한 | "Add to Slack" 워크스페이스 관리자 승인 필요 |
| `.env` 키 | `SLACK_WEBHOOK_URL` |

**단계**:
1. Slack workspace → "Apps" → "Incoming Webhooks" 추가
2. 채널 선택 → Webhook URL 복사
3. `.env`: `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`

### 2.3 카카오 알림톡 (Kakao Bizmessage)

가장 복잡 — 사업자등록증 + 카카오톡 채널 필요:

| 단계 | 내용 |
|------|------|
| 1 | 카카오 비즈니스 채널 (https://accounts.kakao.com/login) 사업자 가입 |
| 2 | 발신 프로필(@channel) 생성 + 인증 |
| 3 | 알림톡 템플릿 사전 등록 + 카카오 검수 (영업일 3~7일) |
| 4 | NHN Cloud Notification 가입 (https://www.toast.com/) |
| 5 | NHN Cloud 콘솔 → AppKey + Secret Key 발급 |

`.env`:
```env
KAKAO_NHN_APPKEY=<NHN 콘솔에서 복사>
KAKAO_NHN_SECRET=<NHN 콘솔에서 복사>
KAKAO_SENDER_KEY=<카카오 발신 프로필 키>
KAKAO_TEMPLATE_BID_DIGEST=<승인된 템플릿 코드>
```

---

## 3. Docker Desktop (Neo4j PoC + 향후 컴포저)

| 항목 | 내용 |
|------|------|
| 다운로드 | https://www.docker.com/products/docker-desktop/ |
| Windows 권장 | WSL2 backend |
| 디스크 요구 | 최소 4GB (Neo4j + GDS plugin) |

**Neo4j PoC 가동**:
```powershell
# Docker Desktop 실행 후
cd deploy/neo4j-poc
docker compose up -d
# 약 30초 후
python scripts/verify_neo4j_poc.py
# 5/5 쿼리 PASS 시 PoC 검증 완료
```

브라우저: http://localhost:7474 (neo4j / govprocu_poc)

---

## 4. ML 학습 (선택) — 자체 검증 완료, 사용자는 실 데이터로 재학습

자율 v3 라운드에서 합성 dataset 500 row + GridSearchCV + SHAP 통합 동작은 검증 완료.

**실 데이터로 재학습 단계**:
```bash
# 0. ML 의존성 (이미 설치됨)
pip install -e ".[ml]"

# 1. 실 dataset 생성 (G2B 키 + ETL 누적 후)
python -m app.ml.dataset --days 90

# 2. baseline 학습
python -m app.ml.train

# 3. 정밀 학습 (GridSearchCV + SHAP)
python -m app.ml.train_v2

# 산출:
# - runtime/ml/model_award_rate_v2.txt (LightGBM 모델)
# - runtime/ml/model_meta_v2.json (best_params, metrics)
# - runtime/ml/shap_summary.json (feature importance)
```

---

## 5. 진행 추적 매트릭스

| 트랙 | 발급 처 | 사용자 액션 | 자동 전환 |
|------|---------|------------|----------|
| LH OpenAPI | data.go.kr | 활용신청 → 인증키 복사 | `.env` 후 ETL 다음 사이클 |
| EX OpenAPI | data.go.kr | 동일 | 동일 |
| KWater OpenAPI | data.go.kr | 동일 | 동일 |
| Korail OpenAPI | data.go.kr | 동일 | 동일 |
| SMTP | Gmail/SES/SG/MG | App Password / IAM | `.env` + 재시작 |
| Slack | api.slack.com | Webhook 생성 | `.env` + 재시작 |
| Kakao 알림톡 | 카카오 + NHN | 비즈니스 가입 + 템플릿 검수 + AppKey | `.env` + 재시작 |
| Docker Desktop | docker.com | 설치 + 실행 | `docker compose up` |
| ML 재학습 | (해당 없음) | dataset/train 실행 | 즉시 |

자율 모드 v3 작성: 2026-05-02. 별도 사용자 작업 시점관리는 `docs/SESSION-SUMMARY-2026-05-02-v3.md` §3 참조.
