# GovProcu — 나라장터 API MCP 서버

> 정부·공공기관 시스템 구축사업 PM이 G2B(나라장터) 데이터를 LLM(Claude 등)으로 자연어 질의·분석할 수 있도록 하는 MCP(Model Context Protocol) 서버.

[![CI](https://github.com/lapiogga/govProcu/actions/workflows/ci.yml/badge.svg)](https://github.com/lapiogga/govProcu/actions/workflows/ci.yml)

## 빠른 시작 (로컬 개발)

```bash
# 1. 환경변수 준비
cp .env.example .env
# .env 파일에 발급받은 G2B 키 6종 입력

# 2. Docker Compose로 기동
cd deploy
docker compose up -d

# 3. 동작 확인
curl http://localhost:8080/mcp/v1/tools  # 등록된 도구 목록
```

## Claude Desktop 연결

`claude_desktop_config.json`에 다음 추가:
```json
{
  "mcpServers": {
    "govprocu": {
      "url": "http://your-server:8080/mcp",
      "transport": "http",
      "headers": { "Authorization": "Bearer <MCP_API_TOKEN>" }
    }
  }
}
```

## 프로젝트 구조

```
GovProcu/
├── app/                          # 애플리케이션
│   ├── server.py                 # FastMCP 진입점
│   ├── config.py                 # 환경변수 로딩
│   ├── clients/g2b.py            # G2B HTTP 클라이언트 (재시도/백오프)
│   ├── core/                     # 캐시·rate limit·인증·에러 정규화
│   ├── schemas/                  # Pydantic 입출력 스키마
│   └── tools/                    # MCP 도구 (영역별)
├── deploy/                       # Dockerfile, docker-compose
├── .github/workflows/ci.yml      # GitHub Actions CI
├── tests/                        # 단위·통합 테스트
├── docs/                         # 기획·설계 문서
│   ├── 나라장터_MCP_서버_구축_계획서.docx
│   ├── 공공데이터포털_나라장터_API_활용신청_가이드.docx
│   └── API_신청_진행_트래커.md
├── logs/                         # 작업·터미널 시계열 로그
└── scripts/                      # 빌드 스크립트
```

## 연동 API (6종)

| 영역 | API | 도구 |
|------|-----|------|
| 입찰공고 | 입찰공고정보서비스 | search_bid_notices, get_bid_notice_detail |
| 사전규격 | 사전규격정보서비스 | list_pre_specifications |
| 낙찰 | 낙찰정보서비스 | get_award_result, search_award_history |
| 사업자 등록 | 입찰참가자격등록정보 | get_vendor_profile |
| 사용자 | 사용자정보서비스 | lookup_user_info |
| 통계 | 공공조달통계정보 | get_procurement_stats |

## 작업 관리 규칙

1. 작업로그: 모든 작업은 `logs/WORK-LOG.md`에 시계열 기록
2. 터미널로그: 모든 셸 명령은 `logs/TERMINAL-LOG.md`에 기록
3. 자동 동기화: 매 20분마다 Cowork 스케줄(`naratjangteo-mcp-worklog-sync`)이 로그·시점관리·GitHub push 수행
4. 시점관리: 작업 완료 시 `logs/WORK-LOG.md` 하단 "다음 작업 시점관리" 표 갱신

## 마일스톤

| 단계 | 기간 | 산출물 | 상태 |
|------|------|--------|------|
| 0. 준비 | Week 1 | API 키 6종 발급 | 5/6 승인 |
| 1. PoC | Week 2-3 | search_bid_notices 도구 동작 | 골격 완료, 키 대기 |
| 2. MVP | Week 4-6 | 11개 도구 + 캐시·인증 | - |
| 3. 운영 | Week 7-8 | Docker 배포본·파일럿 | - |

상세는 [docs/나라장터_MCP_서버_구축_계획서.docx](docs/나라장터_MCP_서버_구축_계획서.docx) 참조.

## 라이선스
사내 사용 한정. 외부 배포 시 별도 협의.
