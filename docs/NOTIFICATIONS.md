# 알림 디스패처 운영 가이드

> `app/dispatcher/` 3채널(email/slack/kakao) 운영 매뉴얼. 환경변수 기반 자동 감지, 채널별 graceful skip.

---

## 1. 채널 우선순위 권장

| 시나리오 | 권장 채널 | 이유 |
|----------|----------|------|
| 개인 사용자 | Email | 별도 계정 불필요, 누락 적음 |
| 팀 구독 | Slack | 채널 broadcast, 스레드 토론 |
| 외부 협력사 | Kakao 알림톡 | 한국 비즈니스 표준, 도달률 높음 |
| 모든 채널 동시 | 3종 모두 | 1차 사용자 설정 시 fan-out |

---

## 2. SMTP (Email) 호스트 결정 가이드

### 2.1 옵션 비교

| 옵션 | 비용 | 설정 난이도 | 권장 시나리오 |
|------|------|------------|-------------|
| **Gmail SMTP** | 무료 | 쉬움 (앱 비밀번호) | 일일 < 500건 |
| **AWS SES** | $0.10/1000건 | 중간 (도메인 검증) | 운영 표준 |
| **SendGrid** | 무료 100건/일 | 쉬움 | 트래킹 필요 |
| **Mailgun** | 무료 5000건/월 | 쉬움 | EU 규정 준수 |
| **사내 Postfix** | 무료 | 어려움 | 보안 정책상 외부 SMTP 차단 시 |

### 2.2 권장: AWS SES (운영) + Gmail (개발)

```bash
# 개발/테스트
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<앱 비밀번호 16자>  # 일반 비번 아님!
SMTP_FROM=your-email@gmail.com
SMTP_USE_TLS=true

# 운영 (AWS SES)
SMTP_HOST=email-smtp.ap-northeast-2.amazonaws.com
SMTP_PORT=587
SMTP_USER=<SES SMTP credential username>
SMTP_PASSWORD=<SES SMTP credential password>
SMTP_FROM=noreply@yourdomain.com  # 검증된 도메인
SMTP_USE_TLS=true
```

### 2.3 검증 명령

```bash
# Python REPL 또는 별도 스크립트
python -c "
import asyncio, os
os.environ['SMTP_HOST']='smtp.gmail.com'
os.environ['SMTP_PORT']='587'
os.environ['SMTP_USER']='your@gmail.com'
os.environ['SMTP_PASSWORD']='xxxx-xxxx-xxxx-xxxx'
os.environ['SMTP_FROM']='your@gmail.com'
from app.dispatcher import send_email
asyncio.run(send_email('to@example.com', 'GovProcu 테스트', '본문'))
print('OK')
"
```

흔한 실패:
- `SMTPAuthenticationError`: Gmail 일반 비번 사용 (앱 비번 발급 필요 — myaccount.google.com → 보안 → 2단계 인증 → 앱 비밀번호)
- `Connection refused`: 사내 방화벽이 587 차단 — IT 팀에 SES IP 화이트리스트 요청
- `Sender address rejected`: SES 도메인 검증 미완료

---

## 3. Slack Incoming Webhook

### 3.1 발급

1. https://api.slack.com/apps → Create New App → From scratch
2. 앱 이름: GovProcu, 워크스페이스 선택
3. Incoming Webhooks → Activate Incoming Webhooks (On)
4. Add New Webhook to Workspace → 채널 선택 (예: #govprocu-alerts)
5. webhook URL 복사 → `.env` 의 `SLACK_WEBHOOK_URL` 에 입력

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxxxxxx
```

### 3.2 사용자별 webhook (override)

`subscriptions` 테이블 row 의 `notify_slack` 컬럼에 사용자 webhook URL 저장 시 우선 적용. 미저장 시 전역 `SLACK_WEBHOOK_URL` 사용.

### 3.3 검증

```bash
python -c "
import asyncio, os
os.environ['SLACK_WEBHOOK_URL']='https://hooks.slack.com/services/...'
from app.dispatcher import send_slack
asyncio.run(send_slack(None, 'GovProcu 테스트 메시지'))
print('OK')
"
```

---

## 4. Kakao 알림톡

> 📌 **카카오 알림톡은 비즈니스 채널 등록 + 발송 대행사 계약 필수.** 자세한 구현은 §6 참조. 즉시 사용 가능한 채널은 아니다.

### 4.1 도입 단계

| 단계 | 작업 | 비용/소요 |
|------|------|----------|
| 1 | 카카오 비즈니스 채널 개설 (business.kakao.com) | 무료, 1일 |
| 2 | 사업자등록번호 인증 | 무료, 즉시 |
| 3 | 발송 대행사 계약 (NHN Cloud / Aligo / Bizppurio 중 택일) | 가입비 무료, 건당 6~10원 |
| 4 | 알림톡 템플릿 등록 → 카카오 검수 (1~3 영업일) | 무료, 검수 통과 필수 |
| 5 | 대행사 API 키 발급 + 환경변수 설정 | 즉시 |

### 4.2 권장 대행사: NHN Cloud Notification

- 안정성 + 한국어 문서 풍부
- 월 사용량에 따라 단가 인하 (1만건+ 시 7원/건)
- API 형태: REST (POST + JSON body)

```bash
KAKAO_API_KEY=<NHN Cloud appKey>
KAKAO_SECRET_KEY=<NHN Cloud secretKey>
KAKAO_SENDER_ID=<발신 프로필 ID, @goVprocu 등>
KAKAO_TEMPLATE_CODE=<검수 통과한 템플릿 코드>
```

---

## 5. 통합 검증 — `dispatch_digest()`

```python
import asyncio
from app.dispatcher import dispatch_digest

digest = {
    "date": "2026-05-02",
    "subscription_count": 3,
    "total_match_count": 12,
    "results": [
        {"keyword": "AI 시스템", "match_count": 5, "items": [
            {"title": "AI 챗봇 개발", "inst_name": "행정안전부", "estimated_price": 30000000}
        ]}
    ]
}
result = asyncio.run(dispatch_digest(
    user_token="user1",
    digest=digest,
    notify_email="me@example.com",
    notify_slack=None,  # 전역 SLACK_WEBHOOK_URL 사용
    notify_kakao=None,  # 카카오 미사용
))
print(result)
# → {"email": "sent", "slack": "sent", "kakao": "skipped"}
```

### 5.1 결과 코드

| status | 의미 | 사용자 액션 |
|--------|------|----------|
| `sent` | 정상 발송 | — |
| `skipped` | 채널 인자 없음 + 전역 환경변수 없음 | 정상 (의도적 미설정) |
| `error: ...` | 발송 시도 실패 | 로그 확인 + 환경변수 점검 |

---

## 6. 운영 정책

### 6.1 발송 빈도 제한

`subscriptions.last_sent_at` 컬럼으로 사용자당 1일 1회 디지스트 강제 (중복 방지).

### 6.2 실패 retry 정책

현재는 **재시도 없음**. 실패 row는 `digest_log` 에 status=error 로 누적.
운영 시 cron 재시도 정책 검토:

```sql
-- 24시간 내 error 만 재시도, 같은 사용자 3회 이상이면 자동 skip
SELECT user_token, channel FROM digest_log
WHERE status LIKE 'error%'
  AND created_at >= DATETIME('now', '-1 day')
  AND user_token NOT IN (
    SELECT user_token FROM digest_log
    WHERE status LIKE 'error%' AND created_at >= DATETIME('now', '-1 day')
    GROUP BY user_token HAVING COUNT(*) >= 3
  );
```

### 6.3 실패 알림 (운영자 대상)

운영자에게 메타 알림: `digest_log` 에 24시간 동안 error >= 10건 발생 시 운영자 Slack 채널로 자동 통지. cron으로 별도 스크립트 운영 (스코프 외).

### 6.4 PII 보호

- email/slack 본문에 사업자등록번호 마스킹 권장 (예: `123-45-67890` → `123-45-****0`)
- 디지스트 본문에 사용자 토큰 노출 금지

---

## 7. 트러블슈팅 빠른 검색

| 증상 | §참조 | 핵심 명령 |
|------|------|----------|
| Gmail 인증 실패 | §2.3 | 앱 비밀번호 발급 |
| SES bounce | §2.2 | 도메인 검증 + DKIM 활성화 |
| Slack 401 | §3.1 | webhook URL 재발급 |
| 카카오 템플릿 거부 | §4.1 | 변수 형식 (#{변수명}) 정확히 입력 |
| `dispatch_digest` 모두 skipped | §5 | 환경변수 어느 것도 미설정 |

작성: 2026-05-02 · `app/dispatcher/` 운영 매뉴얼
