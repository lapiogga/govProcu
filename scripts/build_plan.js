// 나라장터 MCP 서버 구축 계획서 생성 스크립트
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
  TabStopType, TabStopPosition,
} = require('docx');

// ===== 공통 헬퍼 =====
const FONT = "맑은 고딕";
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function P(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 100, line: 320 },
    ...opts,
    children: [new TextRun({ text, font: FONT, size: 22, ...(opts.run || {}) })],
  });
}

function H1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, font: FONT, size: 32, bold: true, color: "1F3864" })],
  });
}

function H2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, font: FONT, size: 26, bold: true, color: "2E75B6" })],
  });
}

function H3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, font: FONT, size: 23, bold: true, color: "404040" })],
  });
}

function Bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 60, line: 300 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function BulletRich(runs, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 60, line: 300 },
    children: runs.map(r => new TextRun({ font: FONT, size: 22, ...r })),
  });
}

function Numbered(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "numbers", level },
    spacing: { after: 60, line: 300 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}

// 셀 만들기
function cell(text, opts = {}) {
  const widthDxa = opts.width;
  const isHeader = opts.header || false;
  const align = opts.align || AlignmentType.LEFT;
  const fill = isHeader ? "1F3864" : (opts.fill || null);
  const color = isHeader ? "FFFFFF" : "000000";
  const lines = Array.isArray(text) ? text : [text];
  return new TableCell({
    borders,
    width: { size: widthDxa, type: WidthType.DXA },
    margins: cellMargins,
    ...(fill ? { shading: { fill, type: ShadingType.CLEAR } } : {}),
    children: lines.map(line => new Paragraph({
      alignment: align,
      spacing: { after: 40, line: 280 },
      children: [new TextRun({ text: line, font: FONT, size: 20, bold: isHeader, color })],
    })),
  });
}

function buildTable(columnWidths, headerRow, dataRows) {
  const totalWidth = columnWidths.reduce((a, b) => a + b, 0);
  const rows = [];
  rows.push(new TableRow({
    tableHeader: true,
    children: headerRow.map((t, i) => cell(t, { width: columnWidths[i], header: true, align: AlignmentType.CENTER })),
  }));
  dataRows.forEach((row, idx) => {
    const fill = idx % 2 === 1 ? "F2F2F2" : null;
    rows.push(new TableRow({
      children: row.map((t, i) => cell(t, { width: columnWidths[i], fill })),
    }));
  });
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths,
    rows,
  });
}

function spacer() {
  return new Paragraph({ spacing: { after: 120 }, children: [new TextRun("")] });
}

// ===== 문서 본문 시작 =====
const children = [];

// 표지
children.push(new Paragraph({
  spacing: { before: 2400, after: 200 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "나라장터 API 연동", font: FONT, size: 56, bold: true, color: "1F3864" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 800 },
  children: [new TextRun({ text: "MCP 서버 구축 계획서", font: FONT, size: 56, bold: true, color: "1F3864" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
  children: [new TextRun({ text: "G2B OpenAPI 기반 LLM Tool Server 구축 사전 기획", font: FONT, size: 26, italics: true, color: "595959" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 2400, after: 100 },
  children: [new TextRun({ text: "Version 1.0", font: FONT, size: 24, color: "404040" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 100 },
  children: [new TextRun({ text: "작성일: 2026-04-29", font: FONT, size: 24, color: "404040" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "기술 스택: Python / FastMCP / HTTP·SSE", font: FONT, size: 24, color: "404040" })],
}));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 1. 프로젝트 개요 =====
children.push(H1("1. 프로젝트 개요"));

children.push(H2("1.1 추진 배경"));
children.push(P("공공기관 시스템 구축사업을 추진함에 있어, 사전 입찰정보 수집·경쟁사 분석·과거 낙찰가 분석은 사업 수주 및 적정 사업비 산정에 결정적인 영향을 미친다. 그러나 나라장터(G2B) 웹 화면에서 수작업으로 정보를 수집하는 방식은 다음과 같은 한계를 갖는다."));
children.push(Bullet("동일 키워드/업종에 대한 반복 검색으로 인한 시간 손실"));
children.push(Bullet("입찰공고-낙찰결과-사업자실적의 데이터 단절로 분석 누락"));
children.push(Bullet("사업 기획·제안 단계에서 LLM 기반 자동 분석 활용 불가"));
children.push(P("본 사업은 나라장터 OpenAPI를 표준 MCP(Model Context Protocol) 인터페이스로 추상화하여, Claude를 비롯한 LLM 클라이언트가 자연어로 G2B 데이터를 조회·분석할 수 있는 팀 공용 MCP 서버를 구축하는 것을 목적으로 한다."));

children.push(H2("1.2 목표"));
children.push(Numbered("나라장터 4대 영역(입찰공고·낙찰계약·사업자실적·통계분석) OpenAPI를 통합한 MCP Tool 서버 구축"));
children.push(Numbered("팀/조직 내 다수 사용자가 동시에 접속 가능한 HTTP·SSE 기반 서버 운영"));
children.push(Numbered("LLM 친화적 도구 시그니처 설계 및 응답 정규화로 활용성 극대화"));
children.push(Numbered("API Rate Limit·캐싱·로깅·인증을 포함한 운영 가능 수준의 안정성 확보"));

children.push(H2("1.3 범위"));
children.push(buildTable(
  [1800, 3600, 3960],
  ["구분", "포함 범위", "비고"],
  [
    ["기능 범위", "입찰공고 검색/상세, 낙찰결과 조회, 계약현황, 사업자 실적·시공능력, 발주 통계", "공공데이터포털 G2B 계열 OpenAPI"],
    ["비기능 범위", "인증, 권한, 캐싱, Rate Limit, 로깅·모니터링, 컨테이너 배포", "팀 단위 공유 환경 전제"],
    ["제외 범위", "G2B 직접 입찰 제출, 전자서명, 전자계약 체결 등 트랜잭션 행위", "법·제도상 별도 인증 필요"],
    ["사용자", "사내 PM, 사업기획팀, 영업·제안팀 (5~30명 수준)", "확장 시 SSO 연계 검토"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 2. 나라장터 OpenAPI 분석 =====
children.push(H1("2. 나라장터 OpenAPI 사전 분석"));

children.push(H2("2.1 API 제공 체계"));
children.push(P("나라장터(G2B)의 정보는 조달청이 공공데이터포털(data.go.kr)을 통해 OpenAPI 형태로 제공한다. 본 MCP 서버가 연동할 주요 API 카테고리는 다음과 같다."));

children.push(buildTable(
  [2200, 3600, 3560],
  ["영역", "대표 API명", "활용 목적"],
  [
    ["입찰공고", "조달청_나라장터 입찰공고정보서비스", "공고 목록·상세, 변경공고, 사전규격, 긴급공고 조회"],
    ["낙찰정보", "조달청_나라장터 낙찰정보서비스", "낙찰자/낙찰가/투찰현황 조회, 경쟁률 분석"],
    ["계약정보", "조달청_나라장터 계약정보서비스", "계약체결 내역, 수의계약·종합쇼핑몰 거래"],
    ["사업자정보", "조달청_나라장터 입찰참가자격등록정보 / 실적정보", "업체 등록정보, 시공능력평가, 실적 조회"],
    ["통계", "조달청_공공조달통계정보 / 발주계획정보", "기관별·업종별·연도별 발주·계약 통계"],
    ["품목/물품", "조달청_나라장터 종합쇼핑몰·물품식별번호", "제품 분류·식별, 단가계약 조회 (보조 기능)"],
  ]
));

children.push(H2("2.2 API 키 발급 절차"));
children.push(P("API 활용신청부터 승인까지의 단계는 다음과 같으며, 본 계획서 단계에서 병행 진행한다."));
children.push(Numbered("공공데이터포털(data.go.kr) 회원가입 (기관 담당자 명의 권장)"));
children.push(Numbered("필요 API 검색 → 활용신청 (위 표의 6개 서비스 모두 신청)"));
children.push(Numbered("일반 인증키(Encoding/Decoding) 발급 — 즉시 발급되나 트래픽 한도 낮음(개발용)"));
children.push(Numbered("운영 키(트래픽 상향) 별도 신청 → 조달청 승인 (영업일 기준 2~5일 소요)"));
children.push(Numbered("개별 API의 활용 승인 상태·일일 트래픽 한도 확인 후 운영 반영"));

children.push(BulletRich([
  { text: "주의: ", bold: true, color: "C00000" },
  { text: "동일 키로 다수 API를 호출하더라도 트래픽 한도는 API별로 별도 산정된다. 운영 단계에서는 기관 명의의 운영키 + 모니터링이 필수다." },
]));

children.push(H2("2.3 기술적 특성 요약"));
children.push(buildTable(
  [2200, 7160],
  ["항목", "내용 / 설계 시 고려사항"],
  [
    ["프로토콜", "HTTP GET, 응답 포맷은 XML / JSON 선택형 (type=json 권장)"],
    ["페이지네이션", "pageNo / numOfRows 파라미터 (보통 numOfRows 최대 999)"],
    ["기간 조회", "공고·계약일자 등에 대해 최소 1일 ~ 최대 1개월 단위 제한이 있는 API 다수"],
    ["응답 안정성", "공공망 특성상 야간 점검·일시 503 발생 빈번 → 재시도/백오프 필수"],
    ["문자 인코딩", "한글 파라미터는 반드시 UTF-8 URL 인코딩"],
    ["서비스키", "URL 쿼리 파라미터 또는 헤더 전달, Encoding 키 사용 시 이중 인코딩 주의"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 3. 요구사항 정의 =====
children.push(H1("3. 요구사항 정의"));

children.push(H2("3.1 기능 요구사항 (FR)"));
children.push(buildTable(
  [1200, 2400, 5760],
  ["ID", "기능명", "상세 설명"],
  [
    ["FR-01", "입찰공고 검색", "키워드, 업종(공사/용역/물품), 지역, 기관명, 공고일·개찰일 범위로 공고 목록 조회"],
    ["FR-02", "입찰공고 상세", "공고번호 기준 상세정보, 첨부파일 메타정보, 사전규격 연계 조회"],
    ["FR-03", "낙찰결과 조회", "공고번호 또는 기간 기준 낙찰자, 낙찰가, 투찰가, 예가 대비율 조회"],
    ["FR-04", "계약 현황", "계약체결 내역 조회 및 수의계약 사유 포함 메타데이터"],
    ["FR-05", "사업자 정보", "사업자번호 기반 등록 업종, 입찰참가자격, 시공능력평가액 조회"],
    ["FR-06", "사업자 실적", "특정 업체의 과거 낙찰·계약 실적 집계"],
    ["FR-07", "통계 조회", "기관별/업종별/연도별 발주·계약 금액 및 건수 집계"],
    ["FR-08", "분석 도구", "경쟁사 비교, 예가 대비율 분포, 키워드 트렌드 등 가공 도구"],
    ["FR-09", "메타 도구", "API 가용성 점검, 캐시 상태, 사용 트래픽 잔량 조회"],
  ]
));

children.push(H2("3.2 비기능 요구사항 (NFR)"));
children.push(buildTable(
  [1200, 2200, 5960],
  ["ID", "항목", "기준"],
  [
    ["NFR-01", "성능", "단일 도구 호출 P95 응답 3초 이내(캐시 적중 시 300ms 이내)"],
    ["NFR-02", "동시성", "동시 활성 사용자 30명, 초당 요청 50 RPS까지 안정 처리"],
    ["NFR-03", "가용성", "월간 가용성 99% (공공API 장애 제외)"],
    ["NFR-04", "보안", "API 키·인증정보는 환경변수/시크릿 매니저 분리, 사용자 인증 토큰 적용"],
    ["NFR-05", "Rate Limit", "공공데이터포털 한도의 80% 도달 시 클라이언트에 경고 응답"],
    ["NFR-06", "관측성", "구조화 로그(JSON) + 도구별 호출 카운트 / 지연 메트릭 수집"],
    ["NFR-07", "운영성", "Docker 기반 단일 명령 배포, 환경분리(dev/stg/prod)"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 4. 시스템 아키텍처 =====
children.push(H1("4. 시스템 아키텍처"));

children.push(H2("4.1 전체 구성"));
children.push(P("본 MCP 서버는 LLM 클라이언트(Claude Desktop, Claude Code, Cowork 등)와 나라장터 OpenAPI 사이의 표준 게이트웨이 역할을 수행한다. 주요 구성요소는 다음 4개 계층이다."));

children.push(buildTable(
  [2000, 7360],
  ["계층", "역할 및 구성"],
  [
    ["접속 계층", "HTTP/SSE 엔드포인트(FastMCP), 인증 미들웨어(API Key 또는 OAuth Bearer), CORS·압축"],
    ["도구 계층", "MCP Tool 정의(@mcp.tool), 입력 스키마 검증(Pydantic), 출력 정규화"],
    ["통합 계층", "G2B API 클라이언트(httpx.AsyncClient), 재시도/백오프, Rate Limiter, 응답 캐시(Redis)"],
    ["관측·운영 계층", "구조화 로깅, OpenTelemetry 메트릭, 헬스체크, Docker Compose 배포"],
  ]
));

children.push(H2("4.2 배포 토폴로지"));
children.push(P("팀 공유 환경을 전제로 다음과 같이 배포한다."));
children.push(Bullet("사내 Linux 서버(또는 사내 K8s)에 Docker Compose로 단일 인스턴스 운영(초기)"));
children.push(Bullet("FastMCP를 Streamable HTTP 모드로 기동 (포트 8080) — Claude 클라이언트가 원격 MCP로 연결"));
children.push(Bullet("Redis 컨테이너 1대(캐시 + Rate Limit 토큰 버킷 공유)"));
children.push(Bullet("Reverse Proxy(Nginx/Caddy)로 TLS 종단 및 사용자 인증 토큰 검증"));
children.push(Bullet("운영 안정화 후 컨테이너 2대로 수평 확장(세션 어피니티는 SSE 특성상 권장)"));

children.push(H2("4.3 디렉터리 구조 (제안)"));
children.push(buildTable(
  [3500, 5860],
  ["경로", "설명"],
  [
    ["/app/server.py", "FastMCP 인스턴스 및 도구 등록 진입점"],
    ["/app/tools/bid.py", "입찰공고 도구 모음 (FR-01, FR-02)"],
    ["/app/tools/award.py", "낙찰·계약 도구 (FR-03, FR-04)"],
    ["/app/tools/vendor.py", "사업자·실적 도구 (FR-05, FR-06)"],
    ["/app/tools/stats.py", "통계·분석 도구 (FR-07, FR-08)"],
    ["/app/clients/g2b.py", "G2B API 비동기 HTTP 클라이언트"],
    ["/app/core/cache.py", "Redis 기반 캐시 데코레이터"],
    ["/app/core/rate_limit.py", "토큰 버킷 Rate Limiter"],
    ["/app/core/auth.py", "사용자 인증 미들웨어"],
    ["/app/schemas/", "Pydantic 입출력 스키마"],
    ["/tests/", "단위 + 통합 테스트(VCR/cassette)"],
    ["/deploy/", "Dockerfile, docker-compose.yml, nginx.conf"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 5. MCP 도구 설계 =====
children.push(H1("5. MCP 도구(Tool) 설계"));

children.push(P("LLM이 자연어로 호출할 도구는 명확한 입력 스키마, 일관된 출력 구조, 적절한 description을 갖추어야 한다. 각 영역별 핵심 도구는 다음과 같다."));

children.push(H2("5.1 입찰공고 영역"));
children.push(buildTable(
  [2400, 3000, 3960],
  ["도구명", "주요 입력", "반환"],
  [
    ["search_bid_notices", "keyword, biz_type(공사/용역/물품), region, date_from, date_to, limit", "공고 요약 리스트(공고번호, 제목, 기관, 추정가, 마감일)"],
    ["get_bid_notice_detail", "bid_no, bid_ord(차수)", "상세항목, 첨부 메타, 입찰방식, 낙찰자결정방법"],
    ["list_pre_specifications", "keyword, date_from, date_to", "사전규격공개 목록 (사전영업·기획용)"],
    ["list_amended_notices", "bid_no", "변경공고/연기공고 이력"],
  ]
));

children.push(H2("5.2 낙찰·계약 영역"));
children.push(buildTable(
  [2400, 3000, 3960],
  ["도구명", "주요 입력", "반환"],
  [
    ["get_award_result", "bid_no, bid_ord", "낙찰자, 낙찰가, 예가, 투찰자수, 낙찰률"],
    ["search_award_history", "keyword/inst_code/date range", "유사 공고의 낙찰 이력 목록"],
    ["search_contracts", "inst_code, date range, biz_type", "계약체결 내역(계약번호, 업체, 금액, 기간)"],
    ["get_contract_detail", "contract_no", "계약 상세 + 수의계약 사유"],
  ]
));

children.push(H2("5.3 사업자·실적 영역"));
children.push(buildTable(
  [2400, 3000, 3960],
  ["도구명", "주요 입력", "반환"],
  [
    ["get_vendor_profile", "biz_reg_no(사업자번호)", "등록업종, 대표자, 입찰참가자격, 시공능력평가액"],
    ["list_vendor_awards", "biz_reg_no, year_range", "해당 업체의 낙찰·계약 실적 집계"],
    ["compare_vendors", "biz_reg_no_list", "복수 업체의 실적·낙찰률·평균 낙찰가 비교"],
  ]
));

children.push(H2("5.4 통계·분석 영역"));
children.push(buildTable(
  [2400, 3000, 3960],
  ["도구명", "주요 입력", "반환"],
  [
    ["get_procurement_stats", "year, inst_code, biz_type", "발주·계약 금액·건수 집계"],
    ["analyze_bid_competition", "keyword/inst_code, date range", "평균 투찰자수, 낙찰률 분포, 표준편차"],
    ["trend_keyword_volume", "keyword, granularity(월/분기)", "키워드별 공고건수 시계열"],
    ["forecast_publication", "inst_code, biz_type", "발주계획 기반 향후 공고 예측 리스트"],
  ]
));

children.push(H2("5.5 도구 설계 원칙"));
children.push(BulletRich([{ text: "명사형/동사형 일관성: ", bold: true }, { text: "조회는 get_/search_/list_, 가공은 analyze_/compare_/forecast_ 접두사 사용." }]));
children.push(BulletRich([{ text: "출력 정규화: ", bold: true }, { text: "G2B XML/JSON의 컬럼명을 LLM 친화적 영문 snake_case로 매핑, 한글 라벨은 별도 필드로 동봉." }]));
children.push(BulletRich([{ text: "결과 요약 동봉: ", bold: true }, { text: "list 결과는 total_count, returned_count, has_more, next_cursor를 포함." }]));
children.push(BulletRich([{ text: "오류 표준화: ", bold: true }, { text: "G2B 에러코드를 카테고리(rate_limit/invalid_param/upstream_5xx)로 변환하여 LLM이 후속 행동을 판단 가능하도록." }]));
children.push(BulletRich([{ text: "Description 한국어 작성: ", bold: true }, { text: "한국어 자연어 호출이 주이므로 도구 description·파라미터 설명은 한국어 + 영문 병기." }]));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 6. 데이터 처리 전략 =====
children.push(H1("6. 데이터 처리 및 운영 전략"));

children.push(H2("6.1 캐싱 전략"));
children.push(buildTable(
  [2400, 1800, 5160],
  ["데이터 종류", "TTL", "근거"],
  [
    ["입찰공고 목록 검색", "5분", "신규 공고 반영 지연 허용 범위"],
    ["입찰공고 상세", "30분", "변경공고 발생 시 별도 무효화"],
    ["낙찰결과", "24시간", "확정 후 변경 거의 없음"],
    ["계약 상세", "24시간", "변경 거의 없음"],
    ["사업자 등록정보", "7일", "등록정보 변경 빈도 낮음"],
    ["통계 데이터", "1일", "월·분기 단위 집계 특성"],
  ]
));
children.push(P("캐시 키는 (도구명 + 정규화된 파라미터 해시) 형태로 구성한다. 동일 사용자/세션의 반복 질의를 효과적으로 차단할 수 있다."));

children.push(H2("6.2 Rate Limit / 재시도"));
children.push(Bullet("공공데이터포털 한도 대비 80% 도달 시 LLM에 \"잔량 부족\" 응답으로 재시도 회피 유도"));
children.push(Bullet("upstream 5xx 발생 시 지수 백오프(1s → 2s → 4s, 최대 3회) 후 실패 처리"));
children.push(Bullet("토큰 버킷은 Redis로 공유하여 다중 인스턴스에서도 한도 정합성 유지"));

children.push(H2("6.3 보안 및 인증"));
children.push(Bullet("MCP 서버 자체 인증: 사용자별 발급 API Token (Bearer) — 사내 ID와 1:1 매핑"));
children.push(Bullet("G2B 서비스키는 환경변수 또는 Vault/Secrets Manager로 분리 (코드/이미지에 미포함)"));
children.push(Bullet("사용자 호출 로그는 사용자ID·도구명·파라미터 해시·응답코드 단위로 기록 (감사 추적)"));
children.push(Bullet("개인정보(사업자 대표자명 등)는 응답 시 마스킹 옵션 제공"));

children.push(H2("6.4 관측성 / 모니터링"));
children.push(Bullet("로그: JSON 구조화 로그, 사용자ID/요청ID/도구명/소요시간/캐시적중 여부"));
children.push(Bullet("메트릭: 도구별 호출수·실패율·P95 지연·G2B 잔여 한도"));
children.push(Bullet("알림: G2B 503 연속 5회 / 한도 90% 도달 / 도구 실패율 5% 초과 시 Slack/Webhook"));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 7. 단계별 추진 계획 =====
children.push(H1("7. 단계별 추진 계획"));

children.push(P("총 8주 일정으로 PoC → MVP → 운영 전환의 3단계로 추진한다."));

children.push(H2("7.1 마일스톤"));
children.push(buildTable(
  [1200, 1600, 2400, 4160],
  ["단계", "기간", "산출물", "주요 활동"],
  [
    ["0. 준비", "1주차", "API 키, 계정, 환경", "공공데이터포털 활용신청·승인 대기, 서버·도메인 확보, 저장소·CI 셋업"],
    ["1. PoC", "2~3주차", "단일 도구 동작본", "FastMCP 골격, search_bid_notices 1개 구현, Claude Desktop 연결 검증"],
    ["2. MVP", "4~6주차", "4개 영역 도구 + 캐시", "11개 핵심 도구 구현, Redis 캐시·Rate Limit, 인증 미들웨어"],
    ["3. 운영", "7~8주차", "Docker 배포본·운영 문서", "TLS·도메인·모니터링 연동, 사용자 매뉴얼, 파일럿 운영"],
  ]
));

children.push(H2("7.2 단계별 종료 조건 (Exit Criteria)"));
children.push(BulletRich([{ text: "PoC: ", bold: true }, { text: "Claude에서 \"최근 일주일 정보화 용역 공고 알려줘\" 자연어 질의에 정상 응답" }]));
children.push(BulletRich([{ text: "MVP: ", bold: true }, { text: "11개 도구 단위테스트 통과율 90% 이상, 동시 5명 사용에서 P95 < 3초" }]));
children.push(BulletRich([{ text: "운영: ", bold: true }, { text: "1주 파일럿 무중단, 사용자 만족도 설문 4.0/5.0 이상" }]));

children.push(H2("7.3 역할 및 책임 (RACI)"));
children.push(buildTable(
  [2400, 1400, 1400, 1400, 2760],
  ["활동", "PM", "개발", "보안", "사용자(파일럿)"],
  [
    ["요구사항 확정", "R/A", "C", "C", "C"],
    ["API 발급·계약", "R/A", "I", "C", "I"],
    ["도구 개발", "C", "R/A", "I", "I"],
    ["보안 검토", "C", "C", "R/A", "I"],
    ["파일럿 검증", "A", "C", "I", "R"],
    ["운영 인계", "R/A", "R", "C", "I"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 8. 리스크 =====
children.push(H1("8. 주요 리스크 및 대응"));

children.push(buildTable(
  [800, 2400, 1200, 1200, 3760],
  ["ID", "리스크", "발생가능성", "영향도", "대응방안"],
  [
    ["R-01", "운영 트래픽 한도 부족", "중", "상", "운영키 사전 신청·반려 시 분할 키 운용, 캐시 TTL 상향"],
    ["R-02", "공공API 점검·장애", "상", "중", "재시도/백오프, 캐시 폴백, 점검 일정 사전 공지"],
    ["R-03", "응답 스키마 변경", "중", "중", "응답 정규화 계층 격리, 통합테스트 카세트 갱신 주기화"],
    ["R-04", "사용자 인증 누수", "하", "상", "Bearer 토큰 정기 로테이션, 감사 로그 보관"],
    ["R-05", "도구 과다로 LLM 혼선", "중", "중", "기능 묶음별 toolset 분리, description 정교화"],
    ["R-06", "사업자 개인정보 노출", "하", "상", "마스킹 기본 적용, 비식별 옵션 제공"],
    ["R-07", "PoC→MVP 일정 지연", "중", "중", "도구 우선순위 P1/P2 분리, P2는 운영 후 점진 추가"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 9. 산출물 및 다음 단계 =====
children.push(H1("9. 산출물 및 다음 단계"));

children.push(H2("9.1 단계별 산출물"));
children.push(Bullet("기획: 요구사항 명세서, 본 계획서, 도구 카탈로그(v1)"));
children.push(Bullet("개발: 소스 저장소(Git), API 매핑 스펙시트, 테스트 카세트"));
children.push(Bullet("운영: Dockerfile/Compose, 운영 매뉴얼, 모니터링 대시보드"));
children.push(Bullet("교육: 사용자 가이드(자연어 질의 예시집), 도구별 한 줄 설명"));

children.push(H2("9.2 다음 액션 (Week 1 Action Items)"));
children.push(Numbered("공공데이터포털 기관 명의 회원가입 및 6개 API 활용신청 (담당자 지정)"));
children.push(Numbered("개발/운영 서버 사양 확정 및 사내 네트워크 정책 협의"));
children.push(Numbered("FastMCP·Redis·httpx 기반 골격 저장소 생성 및 CI(GitHub Actions) 셋업"));
children.push(Numbered("도구 카탈로그 v1 검토회 (사업기획·영업팀 참여, 우선순위 P1/P2 확정)"));
children.push(Numbered("파일럿 사용자 그룹(5명) 선정 및 일정 공유"));

children.push(H2("9.3 향후 확장 후보"));
children.push(Bullet("타 조달 사이트 연동 (LH·코레일 등 자체 입찰사이트 스크레이퍼)"));
children.push(Bullet("내부 제안서 DB와 연계한 \"맞춤 공고 추천\" 도구"));
children.push(Bullet("발주 계획 기반 알림(Webhook → 사내 메신저) 자동화"));
children.push(Bullet("사내 SSO(OIDC) 연동 및 RBAC 도입"));

// ===== 문서 메타 =====
const doc = new Document({
  creator: "라피오자",
  title: "나라장터 API 연동 MCP 서버 구축 계획서",
  description: "G2B OpenAPI 기반 MCP Tool Server 구축 사전 기획",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: "1F3864" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true, color: "2E75B6" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 23, bold: true, color: "404040" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 480, hanging: 240 } } } },
          { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 960, hanging: 240 } } } },
        ] },
      { reference: "numbers",
        levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 480, hanging: 240 } } } },
        ] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "나라장터 MCP 서버 구축 계획서", font: FONT, size: 18, color: "808080" })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "- ", font: FONT, size: 18, color: "808080" }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" }),
            new TextRun({ text: " -", font: FONT, size: 18, color: "808080" }),
          ],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/sessions/determined-dazzling-mendel/mnt/outputs/나라장터_MCP_서버_구축_계획서.docx", buf);
  console.log("OK");
});
