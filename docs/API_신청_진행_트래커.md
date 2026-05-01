# 공공데이터포털 6개 API 활용신청 — 진행 트래커

> 화면 옆에 띄워놓고 진행하세요. 각 API에 대해 ① 검색·진입 → ② 신청서 작성(아래 표준 답변 복붙) → ③ 키 발급 확인 → ④ curl 테스트 → ⑤ `.env`에 등록 순으로 처리합니다.
> 완료한 항목은 `[ ]`을 `[x]`로 바꿔주세요. 자동 sync로 GitHub에 반영됩니다.

---

## 0. 사전 준비 (Step 1·2)

- [ ] 공공데이터포털 회원가입 — https://www.data.go.kr/
- [ ] 본인인증 완료 (휴대폰 또는 공동인증서)
- [ ] 마이페이지 진입 가능 확인 — https://www.data.go.kr/mypage/

---

## 1. 표준 답변 (6개 API 공통, 그대로 복붙)

신청서 진입 시 다음 항목들이 나옵니다. **회색 박스 안 텍스트를 그대로 복사해서 붙여넣으세요.** `[기관명]`만 본인 소속으로 교체.

### 활용 목적 구분
```
기타 (LLM 기반 사내 의사결정지원 시스템)
```

### 활용 목적 (상세)
```
[기관명/사업명]에서 정부·공공기관 시스템 구축사업의 사전 시장조사 및 의사결정 지원을 위해, 사내 LLM(MCP) 서버에 본 API를 연동하여 입찰공고·낙찰결과·사업자실적·통계 데이터를 자연어로 조회·분석할 수 있도록 함. 본 시스템은 사내 PM·기획·영업 인력 약 30명이 사용하며, 외부 공개·재배포는 하지 않음.
```

### 활용 시스템 구분
```
기타 (Internal MCP Server / LLM Tool Backend)
```

### 활용 시스템 명
```
GovProcu MCP Server
```

### 서비스 URL
```
(개발 단계 - 미공개. 사내망 운영 예정)
```

### 서비스 유형
```
기타 (사내 의사결정지원, 비공개)
```

### 일일 트래픽
- 개발: `1,000`
- 운영: `10,000`

### 활용 기간
```
신청일로부터 24개월
```

---

## 2. API별 진행 상황

각 API 카드의 ① 검색 링크 → ② 신청 → ③ 키 발급 → ④ 테스트 순서로 진행하세요.

### ② 입찰공고정보서비스 (BidPublicInfoService)

- [ ] 검색·진입: https://www.data.go.kr/data/15129394/openapi.do
  *(검색이 안되면 검색창에 "나라장터 입찰공고")*
- [ ] 활용신청 클릭 → 위 표준 답변 입력 → 제출
- [ ] 일반 인증키(Encoding) 발급 확인 (마이페이지 → 인증키 발급현황)
- [ ] curl 테스트 통과
- [ ] `.env`에 `G2B_KEY_BID=...` 추가
- [ ] 운영키 심의 신청 (선택)

**기록란 (체크 시 채우기):**
- 신청 시각:
- 승인 시각:
- 키 마지막 4자리:
- 일일 한도:

---

### ③ 낙찰정보서비스 (ScsbidInfoService)

- [ ] 검색·진입: https://www.data.go.kr/data/15129394/openapi.do (또는 "나라장터 낙찰" 검색)
- [ ] 활용신청 클릭 → 표준 답변 입력 → 제출
- [ ] 키 발급 확인
- [ ] curl 테스트
- [ ] `.env`에 `G2B_KEY_AWARD=...` 추가

**기록란:**
- 신청 시각:
- 승인 시각:
- 키 마지막 4자리:
- 일일 한도:

---

### ④ 계약정보서비스 (CntrctInfoService)

- [ ] 검색·진입: 검색창에 "나라장터 계약"
- [ ] 활용신청 → 표준 답변 → 제출
- [ ] 키 발급 확인
- [ ] curl 테스트
- [ ] `.env`에 `G2B_KEY_CONTRACT=...` 추가

**기록란:**
- 신청 시각:
- 승인 시각:
- 키 마지막 4자리:
- 일일 한도:

---

### ⑤ 입찰참가자격등록정보서비스 (HrcspSsstndrdInfoService)

- [ ] 검색·진입: 검색창에 "입찰참가자격등록"
- [ ] 활용신청 → 표준 답변 → 제출
- [ ] 키 발급 확인
- [ ] curl 테스트
- [ ] `.env`에 `G2B_KEY_VENDOR_REG=...` 추가

**기록란:**
- 신청 시각:
- 승인 시각:
- 키 마지막 4자리:
- 일일 한도:

---

### ⑥ 시공능력평가공시정보서비스 (CconcttSttusInfoService)

- [ ] 검색·진입: 검색창에 "시공능력평가공시"
- [ ] 활용신청 → 표준 답변 → 제출
- [ ] 키 발급 확인
- [ ] curl 테스트
- [ ] `.env`에 `G2B_KEY_VENDOR_CAPA=...` 추가

**기록란:**
- 신청 시각:
- 승인 시각:
- 키 마지막 4자리:
- 일일 한도:

---

### ⑦ 공공조달통계정보서비스 (PblPrcrmntStcInfoService)

- [ ] 검색·진입: 검색창에 "공공조달통계"
- [ ] 활용신청 → 표준 답변 → 제출 (이 API는 활용목적 한 줄 차별화 권장)
- [ ] 키 발급 확인
- [ ] curl 테스트
- [ ] `.env`에 `G2B_KEY_STATS=...` 추가

**기록란:**
- 신청 시각:
- 승인 시각:
- 키 마지막 4자리:
- 일일 한도:

---

## 3. curl 테스트 템플릿

### 입찰공고 (예시)
```bash
curl "http://apis.data.go.kr/1230000/BidPublicInfoService05/getBidPblancListInfoServc?serviceKey=YOUR_ENCODED_KEY&numOfRows=3&pageNo=1&type=json&inqryDiv=1&inqryBgnDt=202604010000&inqryEndDt=202604300000"
```

### 정상 응답 (요약)
```json
{
  "response": {
    "header": { "resultCode": "00", "resultMsg": "NORMAL SERVICE." },
    "body": { "items": [...], "totalCount": ... }
  }
}
```

### 자주 발생 에러
| 응답 | 의미 | 대응 |
|------|------|------|
| `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | 키 등록 전 | 1시간 후 재시도 |
| `LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR` | 일일 한도 초과 | 캐시 + 트래픽 상향 |
| `INVALID_REQUEST_PARAMETER_ERROR` | 파라미터 오류 | 필수항목·날짜 형식 확인 |
| HTTP 503 | 점검 중 | 백오프 후 재시도 |

---

## 4. .env 최종 형태 (목표)

```
G2B_KEY_BID=<encoding key>
G2B_KEY_AWARD=<encoding key>
G2B_KEY_CONTRACT=<encoding key>
G2B_KEY_VENDOR_REG=<encoding key>
G2B_KEY_VENDOR_CAPA=<encoding key>
G2B_KEY_STATS=<encoding key>
```

위 6개 모두 발급되면 P2(PoC: search_bid_notices) 단계로 즉시 진입 가능합니다.

---

## 5. 진행 요약 (자동 갱신 대상)

> 6개 API 모두 발급 완료 시 아래 표가 모두 ✅로 채워집니다.

| # | API | 신청 | 승인 | 테스트 |
|---|-----|------|------|--------|
| ② | 입찰공고 | ✅ | ✅ | ⏳ |
| ③ | 낙찰 | ✅ | ✅ | ⏳ |
| ④ | 계약 | ✅ | ✅ | ⏳ |
| ⑤ | 입찰참가자격 | ⏳ | ⏳ | ⏳ |
| ⑥ | 시공능력평가 | ⏳ | ⏳ | ⏳ |
| ⑦ | 공공조달통계 | ✅ | ✅ | ⏳ |

각 API 진행 후 `⏳`을 `✅`(완료) 또는 `❌`(반려)로 바꿔주시거나, 채팅에 "②번 승인됐어"처럼 알려주시면 제가 표를 갱신하겠습니다.
