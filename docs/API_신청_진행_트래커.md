# 공공데이터포털 나라장터 API 활용신청 — 진행 트래커 v3 (최종 확정)

> 6종 모두 활용신청·승인 완료. 이제 .env에 키 6종 입력 후 PoC 단계 진입.

> **변경이력:**
> - v1: 초기 6종 (입찰공고/낙찰/계약/입찰참가자격/시공능력/통계)
> - v2: ④계약정보·⑥시공능력 제외, 사전규격·사용자정보 추가
> - **v3 (2026-05-01 18:20 KST): D를 입찰참가자격등록 → 계약과정통합공개로 교체. 6종 확정 ✅**

---

## 1. 최종 6종 API (모두 승인 완료)

| # | API 정식명 | 환경변수 | 도구 매핑 |
|---|-----------|---------|-----------|
| A | 조달청_나라장터 입찰공고정보서비스 | `G2B_KEY_BID` | search_bid_notices, get_bid_notice_detail |
| B | 조달청_나라장터 사전규격정보서비스 | `G2B_KEY_PRESPEC` | list_pre_specifications |
| C | 조달청_나라장터 낙찰정보서비스 | `G2B_KEY_AWARD` | get_award_result, search_award_history |
| D | 조달청_나라장터 계약과정통합공개서비스 | `G2B_KEY_CONTRACT` | get_contract_process, search_contracts |
| E | 조달청_나라장터 사용자정보서비스 | `G2B_KEY_USER` | lookup_user_info |
| F | 조달청_공공조달통계정보서비스 | `G2B_KEY_STATS` | get_procurement_stats, analyze_bid_competition |

---

## 2. .env 채우기 체크리스트

`.env` 파일을 텍스트 에디터로 열어 발급받은 6개 Encoding 키를 채워주세요:

```
G2B_KEY_BID=<A의 일반인증키 Encoding>
G2B_KEY_PRESPEC=<B의 일반인증키 Encoding>
G2B_KEY_AWARD=<C의 일반인증키 Encoding>
G2B_KEY_CONTRACT=<D의 일반인증키 Encoding>
G2B_KEY_USER=<E의 일반인증키 Encoding>
G2B_KEY_STATS=<F의 일반인증키 Encoding>
MCP_API_TOKENS=dev-token-replace-me
```

`.env`는 `.gitignore`로 차단되어 GitHub에 절대 노출되지 않습니다.

---

## 3. 진행 요약

| # | API | 신청 | 승인 | 키 .env 입력 | curl 테스트 |
|---|-----|------|------|--------------|-------------|
| A | 입찰공고 | ✅ | ✅ | ⏳ | ⏳ |
| B | 사전규격 | ✅ | ✅ | ⏳ | ⏳ |
| C | 낙찰 | ✅ | ✅ | ⏳ | ⏳ |
| D | 계약과정통합 | ✅ | ✅ | ⏳ | ⏳ |
| E | 사용자정보 | ✅ | ✅ | ⏳ | ⏳ |
| F | 공공조달통계 | ✅ | ✅ | ⏳ | ⏳ |

**6/6 승인 완료 (100%)** 🎉

---

## 4. 다음 단계 — PoC 실행

```powershell
# 1. .env 채우기 (위 표 참고)
notepad C:\Users\User\GovProcu\.env

# 2. Python 의존성 설치
cd C:\Users\User\GovProcu
pip install -e .

# 3. 서버 기동 (개발 모드)
uvicorn app.server:app --port 8081 --reload

# 4. 다른 PowerShell에서 동작 확인
curl http://localhost:8081/health
```

또는 Docker로:
```powershell
cd C:\Users\User\GovProcu\deploy
docker compose up
```
