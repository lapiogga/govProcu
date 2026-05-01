# GovProcu — 나라장터 API MCP 서버

> 정부·공공기관 시스템 구축사업 PM이 G2B(나라장터) 데이터를 LLM(Claude 등)으로 자연어 질의·분석할 수 있도록 하는 MCP(Model Context Protocol) 서버.

## 프로젝트 목표
- 나라장터 OpenAPI 4대 영역(입찰공고/낙찰계약/사업자실적/통계)을 단일 MCP 서버로 통합
- 팀/조직 공유용 HTTP·SSE 기반 운영
- Python(FastMCP) + Redis(캐시·Rate Limit) + Docker 배포

## 디렉터리 구조
```
GovProcu/
├── README.md                    # 본 파일
├── docs/                        # 기획·설계 문서
│   └── 나라장터_MCP_서버_구축_계획서.docx
├── logs/                        # 작업·터미널 시계열 로그
│   ├── WORK-LOG.md
│   └── TERMINAL-LOG.md
├── scripts/                     # 문서·도구 생성 스크립트
│   └── build_plan.js
└── (향후) app/, deploy/, tests/
```

## 작업 관리 규칙
1. **작업로그**: 모든 작업은 `logs/WORK-LOG.md`에 `시작/종료/소요/작업명/내용` 형식 시계열 기록
2. **터미널로그**: 모든 셸 명령은 `logs/TERMINAL-LOG.md`에 `[HH:MM:SS KST] $ <command>` 형식 기록
3. **자동 동기화**: 매 20분마다 Cowork 스케줄(`naratjangteo-mcp-worklog-sync`)이 로그 갱신·시점관리·GitHub push 수행
4. **시점관리**: 작업 완료 시 `logs/WORK-LOG.md` 하단의 "다음 작업 시점관리" 표를 갱신

## 일정 (요약)
| 단계 | 기간 | 산출물 |
|------|------|--------|
| 0. 준비 | Week 1 | 공공데이터포털 API 키, 환경 셋업 |
| 1. PoC | Week 2-3 | search_bid_notices 도구 1개 동작 |
| 2. MVP | Week 4-6 | 11개 도구 + 캐시·인증 |
| 3. 운영 | Week 7-8 | Docker 배포본·파일럿 운영 |

자세한 내용은 [docs/나라장터_MCP_서버_구축_계획서.docx](docs/나라장터_MCP_서버_구축_계획서.docx) 참조.

## 라이선스
사내 사용 한정. 외부 배포 시 별도 협의.
