# 공공데이터포털 나라장터 API 활용신청 — 진행 트래커 v2

> 화면 옆에 띄워놓고 진행하세요. 각 API에 대해 ① 검색·진입 → ② 신청서 작성 → ③ 키 발급 확인 → ④ curl 테스트 → ⑤ `.env` 등록 순으로 처리합니다.
> 완료한 항목은 `[ ]`을 `[x]`로 바꿔주세요. 자동 sync로 GitHub에 반영됩니다.

> **변경이력 (v2, 2026-05-01 17:40 KST):**
> - ④ 계약정보, ⑥ 시공능력평가공시 → **프로젝트 범위에서 제외**
> - 신규 추가: **사전규격정보서비스**, **사용자정보서비스**
> - 최종 6개 API 구성

---

## 1. 표준 답변 (모든 API 공통, 그대로 복붙)

[기관명] 부분만 본인 소속으로 1회 교체.

### 활용 목적 구분
```
기타 (LLM 기반 사내 의사결정지원 시스템)
```

### 활용 목적 (상세)
```
[기관명/사업명]에서 정부·공공기관 시스템 구축사업의 사전 시장조사 및 의사결정 지원을 위해, 사내 LLM(MCP) 서버에 본 API를 연동하여 입찰공고·낙찰결과·사업자실적·통계 데이터를 자연어로 조회·분석할 수 있도록 함. 본 시스템은 사내 PM·기획·영업 인력 약 30명이 사용하며, 외부 공개·재배포는 하지 않음.
```

### 그 외 (공통)
- 활용 시스템 구분: `기타 (Internal MCP Server / LLM Tool Backend)`
- 활용 시스템 명: `GovProcu MCP Server`
- 서비스 URL: `(개발 단계 - 미공개. 사내망 운영 예정)`
- 서비스 유형: `기타 (사내 의사결정지원, 비공개)`
- 일일 트래픽: 개발 `1,000` / 운영 `10,000`
- 활용 기간: `신청일로부터 24개월`

---

## 2. API별 진행 상황 (최종 6종)

### A. 입찰공고정보서비스 (BidPublicInfoService) — 핵심
- [x] 활용신청 / 승인 / 키발급
- [ ] curl 테스트
- [ ] `.env`: `G2B_KEY_BID=...`
- 키 마지막 4자리: ___ / 일일 한도: ___

### B. 사전규격정보서비스 (PreSpecificationInfoService) — 핵심 (신규)
- [x] 활용신청 / 승인 / 키발급
- [ ] curl 테스트
- [ ] `.env`: `G2B_KEY_PRESPEC=...`
- 키 마지막 4자리: ___ / 일일 한도: ___

### C. 낙찰정보서비스 (ScsbidInfoService) — 핵심
- [x] 활용신청 / 승인 / 키발급
- [ ] curl 테스트
- [ ] `.env`: `G2B_KEY_AWARD=...`
- 키 마지막 4자리: ___ / 일일 한도: ___

### D. 입찰참가자격등록정보서비스 (HrcspSsstndrdInfoService) — 사업자
- [ ] 활용신청 / 승인 / 키발급
- [ ] curl 테스트
- [ ] `.env`: `G2B_KEY_VENDOR=...`
- 키 마지막 4자리: ___ / 일일 한도: ___

### E. 사용자정보서비스 (UsrInfoService) — 사업자 보조 (신규)
- [x] 활용신청 / 승인 / 키발급
- [ ] curl 테스트
- [ ] `.env`: `G2B_KEY_USER=...`
- 키 마지막 4자리: ___ / 일일 한도: ___

### F. 공공조달통계정보서비스 (PblPrcrmntStcInfoService) — 통계
- [x] 활용신청 / 승인 / 키발급
- [ ] curl 테스트
- [ ] `.env`: `G2B_KEY_STATS=...`
- 키 마지막 4자리: ___ / 일일 한도: ___

### ❌ 제외된 API (참고용)
- ~~④ 계약정보서비스 (CntrctInfoService)~~ — 프로젝트 범위 제외
- ~~⑥ 시공능력평가공시정보서비스 (CconcttSttusInfoService)~~ — 프로젝트 범위 제외

---

## 3. .env 최종 형태 (6키)

```
G2B_KEY_BID=<encoding key>
G2B_KEY_PRESPEC=<encoding key>
G2B_KEY_AWARD=<encoding key>
G2B_KEY_VENDOR=<encoding key>
G2B_KEY_USER=<encoding key>
G2B_KEY_STATS=<encoding key>
```

---

## 4. 진행 요약

| # | API | 신청 | 승인 | 테스트 | 도구 매핑 |
|---|-----|------|------|--------|-----------|
| A | 입찰공고 | ✅ | ✅ | ⏳ | search_bid_notices, get_bid_notice_detail |
| B | 사전규격 | ✅ | ✅ | ⏳ | list_pre_specifications |
| C | 낙찰 | ✅ | ✅ | ⏳ | get_award_result, search_award_history |
| D | 입찰참가자격 | ⏳ | ⏳ | ⏳ | get_vendor_profile |
| E | 사용자정보 | ✅ | ✅ | ⏳ | lookup_user_info |
| F | 공공조달통계 | ✅ | ✅ | ⏳ | get_procurement_stats, analyze_bid_competition |

**5/6 승인 완료 (83%)** — D(입찰참가자격등록) 1개만 남음.

---

## 5. curl 테스트 템플릿 & 자주 발생 에러
(상세 가이드 docx 참조)
