# GovProcu E2E 테스트

## 시나리오 3종

| # | 파일 | 시나리오 |
|---|------|---------|
| 1 | `01-bid-trace.spec.ts` | 입찰 상세 추적 (영업 매니저) |
| 2 | `02-vendor-profile.spec.ts` | 업체 프로필 (영업/임원) |
| 3 | `03-cross-lookup.spec.ts` | Cross-Lookup + AI 콘솔 (분석가) |

## 실행

```bash
cd frontend
npm install
npx playwright install  # 첫 1회

# 백그라운드: MCP 서버 + frontend dev
# (다른 터미널) cd .. && uvicorn app.server:app --port 8081
# (다른 터미널) npm run dev

# E2E 실행
E2E_TEST_BID_NO=20240315678 E2E_TEST_BIZ_NO=1058705373 npm run test:e2e

# UI 모드 (디버깅)
npm run test:e2e:ui
```

## 환경변수

| 이름 | 기본 | 설명 |
|------|------|------|
| `E2E_BASE_URL` | `http://localhost:3000` | frontend URL |
| `E2E_TEST_BID_NO` | `20240315678` | 추적할 실제 공고번호 |
| `E2E_TEST_BIZ_NO` | `1058705373` | 검증할 실제 사업자번호 |
| `E2E_TEST_INST` | `국방재정관리단` | 분석할 발주기관 |

실 데이터로 테스트하므로 G2B/NTS API 키 활성화 + 운영 IP 필요.

## CI 통합

`.github/workflows/e2e.yml` (TODO):
- main 브랜치 push 시
- macOS/ubuntu Chromium
- artifact 업로드 (trace/screenshot/video)
