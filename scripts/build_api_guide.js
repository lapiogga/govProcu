// 공공데이터포털 나라장터 6개 API 활용신청 가이드 docx 생성
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
} = require('docx');

const FONT = "맑은 고딕";
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function P(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 100, line: 320 }, ...opts,
    children: [new TextRun({ text, font: FONT, size: 22, ...(opts.run || {}) })],
  });
}
function H1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, font: FONT, size: 32, bold: true, color: "1F3864" })],
  });
}
function H2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, font: FONT, size: 26, bold: true, color: "2E75B6" })],
  });
}
function H3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 120 },
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
function Check(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "checks", level },
    spacing: { after: 60, line: 300 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}
function cell(text, opts = {}) {
  const widthDxa = opts.width;
  const isHeader = opts.header || false;
  const align = opts.align || AlignmentType.LEFT;
  const fill = isHeader ? "1F3864" : (opts.fill || null);
  const color = isHeader ? "FFFFFF" : "000000";
  const lines = Array.isArray(text) ? text : [text];
  return new TableCell({
    borders, width: { size: widthDxa, type: WidthType.DXA }, margins: cellMargins,
    ...(fill ? { shading: { fill, type: ShadingType.CLEAR } } : {}),
    children: lines.map(line => new Paragraph({
      alignment: align, spacing: { after: 40, line: 280 },
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
  return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths, rows });
}

const children = [];

// 표지
children.push(new Paragraph({
  spacing: { before: 2400, after: 200 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "공공데이터포털", font: FONT, size: 48, bold: true, color: "1F3864" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [new TextRun({ text: "나라장터 6개 OpenAPI", font: FONT, size: 48, bold: true, color: "1F3864" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 800 },
  children: [new TextRun({ text: "활용신청 실무 가이드", font: FONT, size: 48, bold: true, color: "1F3864" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [new TextRun({ text: "GovProcu MCP 서버 구축 P1 산출물", font: FONT, size: 24, italics: true, color: "595959" })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 100 },
  children: [new TextRun({ text: "Version 1.0  |  2026-05-01", font: FONT, size: 22, color: "404040" })],
}));
children.push(new Paragraph({ children: [new PageBreak()] }));

// 1. 개요
children.push(H1("1. 개요"));
children.push(H2("1.1 본 가이드의 목적"));
children.push(P("본 가이드는 GovProcu MCP 서버가 연동할 나라장터(G2B) 계열 OpenAPI 6종을 공공데이터포털에서 신청·발급·운영 한도 상향까지 진행하는 데 필요한 모든 절차를 단계별로 정리한다. PM이 직접 작성·결재 가능한 수준의 체크리스트와 표준 답변문구를 포함한다."));

children.push(H2("1.2 발급 전체 흐름"));
children.push(buildTable(
  [800, 2200, 2400, 3960],
  ["단계", "단계명", "소요시간", "주요 산출물 / 비고"],
  [
    ["1", "회원가입·본인인증", "30분", "공공데이터포털 회원가입(기관 명의 권장), 휴대폰/공동인증서 본인인증"],
    ["2", "API 6종 검색·확인", "30분", "각 API URL·요청한도·이용허락범위 사전 점검"],
    ["3", "활용신청서 작성·제출", "1~2시간", "API별 활용목적·시스템유형·트래픽 등 입력 (본 가이드 제3장 표준답변 참고)"],
    ["4", "자동승인 키 발급", "즉시", "신청 직후 일반 인증키 발급 (개발용 한도)"],
    ["5", "심의·승인 (운영키)", "영업일 2~5일", "조달청 심의 후 운영 트래픽 부여"],
    ["6", "키 동작 테스트", "30분", "샘플 호출 → JSON 응답 확인 → .env 등록"],
    ["7", "트래픽 모니터링·상향", "수시", "한도 80% 도달 시 트래픽 상향 신청"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 2. 사전 준비
children.push(H1("2. 사전 준비 (Step 1)"));

children.push(H2("2.1 공공데이터포털 회원가입"));
children.push(BulletRich([
  { text: "URL: ", bold: true },
  { text: "https://www.data.go.kr/", color: "2E75B6" },
]));
children.push(Bullet("회원 유형: 일반회원 (기업·기관 회원도 가능, 본 사업은 기관 명의로 권장)"));
children.push(Bullet("ID/PW 외 휴대폰 본인인증 또는 아이핀 인증 필요"));
children.push(BulletRich([
  { text: "권장: ", bold: true, color: "C00000" },
  { text: "PM 개인 명의가 아닌 사업 담당자 그룹메일·기관 대표메일을 활용. 인사이동 시 키 재발급 부담 감소." },
]));

children.push(H2("2.2 본인인증 (활용신청 필수)"));
children.push(P("API 활용신청은 본인인증이 완료된 계정만 가능하다. 다음 중 1개 보유:"));
children.push(Bullet("휴대폰 본인인증 (가장 간단)"));
children.push(Bullet("공동인증서(구 공인인증서) — 기관 명의 권장"));
children.push(Bullet("아이핀(I-PIN)"));

children.push(H2("2.3 마이페이지 메뉴 사전 숙지"));
children.push(buildTable(
  [3000, 6360],
  ["메뉴", "용도"],
  [
    ["마이페이지 → 활용신청 현황", "신청한 API의 승인 상태·키 확인"],
    ["마이페이지 → 인증키 발급현황", "발급된 일반 인증키(Encoding/Decoding) 조회"],
    ["마이페이지 → 트래픽 통계", "일/월 호출량·잔여량·실패율 모니터링"],
    ["마이페이지 → 활용 변경신청", "트래픽 상향, 활용목적 변경, 사용 종료"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 3. 6개 API 상세
children.push(H1("3. 신청 대상 6개 API 상세"));
children.push(P("각 API는 공공데이터포털 검색창에 표의 \"검색 키워드\"를 입력하면 즉시 찾을 수 있다. 모두 조달청이 제공하며, 동일 일반 인증키로 호출 가능하지만 트래픽 한도는 API별로 별도 산정된다."));

children.push(H2("3.1 API 일람"));
children.push(buildTable(
  [400, 2600, 3000, 3360],
  ["#", "API 정식명", "검색 키워드 / 식별자", "용도 (도구 매핑)"],
  [
    ["1", "조달청_나라장터 입찰공고정보서비스", "나라장터 입찰공고", "search_bid_notices, get_bid_notice_detail, list_pre_specifications, list_amended_notices"],
    ["2", "조달청_나라장터 낙찰정보서비스", "나라장터 낙찰", "get_award_result, search_award_history"],
    ["3", "조달청_나라장터 계약정보서비스", "나라장터 계약", "search_contracts, get_contract_detail"],
    ["4", "조달청_나라장터 입찰참가자격등록정보서비스", "입찰참가자격등록", "get_vendor_profile (등록업종·자격)"],
    ["5", "조달청_나라장터 시공능력평가공시정보서비스", "시공능력평가", "get_vendor_profile (시평액), list_vendor_awards 보강"],
    ["6", "조달청_공공조달통계정보서비스", "공공조달통계", "get_procurement_stats, analyze_bid_competition, trend_keyword_volume"],
  ]
));

children.push(H2("3.2 API별 주요 엔드포인트 패턴"));
children.push(P("각 API는 공통적으로 다음과 같은 형태를 가진다 (실제 엔드포인트는 활용신청 후 마이페이지 \"기술문서\"에서 확인):"));
children.push(buildTable(
  [3000, 6360],
  ["요소", "예시 / 형식"],
  [
    ["Base URL", "http://apis.data.go.kr/1230000/<서비스코드>"],
    ["기관코드", "1230000 (조달청)"],
    ["인증 파라미터", "ServiceKey=<발급키> (URL 쿼리, Encoding 형태 권장)"],
    ["페이지 파라미터", "pageNo=1, numOfRows=10 (최대 999)"],
    ["응답 포맷", "type=json (또는 type=xml, 기본 xml)"],
    ["기간 파라미터", "inqryBgnDt=YYYYMMDDHHMM, inqryEndDt=YYYYMMDDHHMM (보통 1개월 한도)"],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 4. 활용신청서 작성 가이드
children.push(H1("4. 활용신청서 작성 가이드 (Step 3)"));

children.push(H2("4.1 신청 화면 진입 경로"));
children.push(Numbered("data.go.kr 검색창에 표의 \"검색 키워드\" 입력"));
children.push(Numbered("결과 목록에서 정확한 정식명 클릭"));
children.push(Numbered("우측 상단 \"활용신청\" 버튼 클릭"));
children.push(Numbered("로그인 + 본인인증 확인 → 신청서 화면 진입"));

children.push(H2("4.2 항목별 표준 답변 (6개 API 공통)"));
children.push(P("아래 답변은 사내 사업 컨텍스트에 맞춰 조정 후 그대로 입력하면 1차 자동승인 + 2차 운영심의 통과 가능성이 높다."));

children.push(buildTable(
  [2400, 6960],
  ["항목", "표준 답변 (필요 시 [   ] 부분만 수정)"],
  [
    ["활용 목적 구분", "기타 (LLM 기반 사내 의사결정지원 시스템)"],
    ["활용 목적 상세", "[기관/사업명]에서 정부·공공기관 시스템 구축사업의 사전 시장조사 및 의사결정 지원을 위해 사내 LLM(MCP) 서버에 본 API를 연동, 입찰공고·낙찰결과·사업자실적·통계 데이터를 자연어로 조회·분석할 수 있도록 함."],
    ["활용 시스템 구분", "기타 (Internal MCP Server / LLM Tool Backend)"],
    ["활용 시스템 명", "GovProcu MCP Server"],
    ["서비스 URL", "(개발 단계 - 미공개. 사내망 운영 예정)"],
    ["서비스 유형", "기타 (사내 의사결정지원, 비공개)"],
    ["일일 트래픽 (예상)", "개발: 1,000건 / 운영: 10,000건 (사내 사용자 약 30명, 캐시 적용 후 실호출)"],
    ["활용 기간", "신청일 ~ 24개월 (자동 갱신 신청 예정)"],
    ["관련 첨부", "(선택) GovProcu_MCP_서버_구축_계획서.docx"],
  ]
));

children.push(H2("4.3 6개 API 모두 동일하게 적용"));
children.push(BulletRich([
  { text: "동일한 답변을 6개 API 신청서에 모두 입력. ", bold: true },
  { text: "단, \"활용 목적 상세\" 부분은 각 API의 데이터 종류를 한 줄씩 차별화하면 심의 통과율이 올라간다." },
]));
children.push(P("예: 입찰공고정보서비스에는 \"입찰공고 메타데이터(공고일자·기관·예가) 조회\", 시공능력평가공시정보서비스에는 \"시평액 기반 사업자 적격성 1차 스크리닝\" 등."));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 5. 승인 후 확인 및 트래픽
children.push(H1("5. 승인 후 확인 및 트래픽 관리"));

children.push(H2("5.1 키 발급 직후 확인사항 (Step 4)"));
children.push(Check("일반 인증키(Encoding) 복사 — `xxx%2B%2F...` 형태"));
children.push(Check("일반 인증키(Decoding) 복사 — `xxx+/...` 형태 (코드에서 직접 인코딩 시 사용)"));
children.push(Check("API별 일일 트래픽 한도 확인 (보통 개발용 1,000건/일)"));
children.push(Check("\"기술문서\" 다운로드 → 엔드포인트·파라미터·에러코드 확인"));

children.push(H2("5.2 동작 테스트 (curl 1줄)"));
children.push(P("입찰공고정보서비스 동작 확인 예시 (Encoding 키 사용):"));
children.push(new Paragraph({
  spacing: { after: 200 },
  children: [new TextRun({
    text: 'curl "http://apis.data.go.kr/1230000/BidPublicInfoService05/getBidPblancListInfoServc?serviceKey=YOUR_ENCODED_KEY&numOfRows=3&pageNo=1&type=json"',
    font: "Consolas", size: 18,
  })],
}));
children.push(P("정상 응답이면 JSON으로 공고 3건이 반환된다. 응답에 SERVICE_KEY_IS_NOT_REGISTERED_ERROR 등이 포함되면 키 미승인 상태."));

children.push(H2("5.3 .env 파일 표준 양식"));
children.push(P("발급받은 키는 GovProcu/.env (또는 시크릿 매니저)에 저장. 6개 키를 동일 변수에 통합하지 말고 API별로 분리:"));
children.push(new Paragraph({
  spacing: { after: 100 },
  children: [new TextRun({
    text: [
      "G2B_KEY_BID=xxx",
      "G2B_KEY_AWARD=xxx",
      "G2B_KEY_CONTRACT=xxx",
      "G2B_KEY_VENDOR_REG=xxx",
      "G2B_KEY_VENDOR_CAPA=xxx",
      "G2B_KEY_STATS=xxx",
    ].join("\n"),
    font: "Consolas", size: 18,
  })],
}));
children.push(BulletRich([
  { text: "권장: ", bold: true, color: "C00000" },
  { text: ".env는 .gitignore에 반드시 포함 (이미 등록됨). 운영에서는 Vault/AWS Secrets Manager로 분리." },
]));

children.push(H2("5.4 트래픽 상향 신청 (Step 7)"));
children.push(P("개발용 1,000건/일은 도구 8~9개를 사용하는 운영 단계에서는 부족하다. 다음 시점에 상향 신청:"));
children.push(Bullet("일일 사용량이 80%에 3회 이상 도달"));
children.push(Bullet("MVP 단계 진입 (사용자 5명 이상 동시 사용 시작)"));
children.push(P("상향 신청 경로: 마이페이지 → 활용 변경신청 → 트래픽 → 사유 작성 + 사용량 그래프 캡처 첨부 → 제출. 일반적으로 영업일 3~7일 내 처리."));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 6. 체크리스트
children.push(H1("6. 신청 진행 체크리스트 (인쇄용)"));
children.push(P("아래 항목을 위에서 아래로 진행. 완료 시 해당 박스에 체크. 6개 API는 같은 단계를 반복."));

children.push(H2("6.1 사전 준비"));
children.push(Check("공공데이터포털 회원가입 (기관 명의 권장)"));
children.push(Check("본인인증 완료 (휴대폰/공동인증서)"));
children.push(Check("관련 부서 결재(필요 시) — 본 가이드 + 계획서 첨부"));

children.push(H2("6.2 API별 신청 (각 API마다 반복)"));
const apis = [
  "1) 조달청_나라장터 입찰공고정보서비스",
  "2) 조달청_나라장터 낙찰정보서비스",
  "3) 조달청_나라장터 계약정보서비스",
  "4) 조달청_나라장터 입찰참가자격등록정보서비스",
  "5) 조달청_나라장터 시공능력평가공시정보서비스",
  "6) 조달청_공공조달통계정보서비스",
];
apis.forEach(api => {
  children.push(Check(`${api} — 검색·신청·키발급·동작테스트 완료`));
});

children.push(H2("6.3 발급 후"));
children.push(Check("6개 키 모두 .env에 저장 (G2B_KEY_BID 등 변수 분리)"));
children.push(Check("curl 1회 호출로 각 API 정상 응답 확인"));
children.push(Check("운영키 심의 신청 (기본 키만 받은 경우)"));
children.push(Check("일일 모니터링 알림 설정 (트래픽 80% 도달 시)"));

children.push(H2("6.4 PM 결재용 산출물"));
children.push(Check("API별 \"기술문서\" PDF 다운로드 → docs/api/ 폴더 보관"));
children.push(Check("발급 화면 캡처 → docs/evidence/ 폴더 보관 (감사 추적)"));
children.push(Check("WORK-LOG.md에 신청 시각·승인 시각·키 마지막 4자리 기록 (전체 키 금지)"));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 7. FAQ / 트러블슈팅
children.push(H1("7. 자주 발생하는 이슈"));

children.push(buildTable(
  [3000, 6360],
  ["증상", "원인 / 대응"],
  [
    ["SERVICE_KEY_IS_NOT_REGISTERED_ERROR", "신청은 완료됐으나 자동승인이 풀리기 전(최대 1시간). 1시간 후 재시도. 그래도 발생 시 마이페이지에서 \"활용신청 상태 = 승인\" 확인."],
    ["응답이 XML로만 옴", "type=json 파라미터 누락. URL 쿼리에 &type=json 추가."],
    ["한글 검색이 결과 0건", "URL 인코딩 누락. UTF-8 → percent-encoding (예: %EA%B1%B4%EC%84%A4)."],
    ["LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR", "일일 한도 초과. 캐시 TTL 상향 + 트래픽 상향 신청."],
    ["응답 5xx 503", "공공망 점검(보통 야간 23:00~06:00). 백오프·재시도로 처리."],
    ["인증키가 두 종류인데 어느 것을 써야 하나", "URL 쿼리에 직접 붙일 때는 Encoding 키, 코드에서 자체 인코딩 시 Decoding 키. 권장: Encoding 키 + 그대로 URL 삽입."],
    ["기술문서가 비어있음", "조달청은 분기별 갱신. 마지막 업데이트 일자 확인 후 나라장터 OpenAPI 공지사항에서 변경분 확인."],
  ]
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 8. 다음 액션
children.push(H1("8. 다음 액션"));
children.push(P("본 가이드에 따라 신청을 진행하면서 GovProcu/logs/WORK-LOG.md에 다음 정보를 기록한다 (자동 sync로 GitHub에 반영)."));
children.push(buildTable(
  [3000, 6360],
  ["기록 항목", "예시"],
  [
    ["신청 시각", "2026-05-02 10:15 KST"],
    ["승인 시각", "2026-05-02 11:08 KST (자동승인)"],
    ["운영키 심의 신청 시각", "2026-05-03 14:00 KST"],
    ["운영키 심의 결과", "2026-05-08 16:30 KST 승인 (영업일 3일)"],
    ["키 마지막 4자리", "...A1b2 (전체 키는 .env에만)"],
    ["일일 한도", "개발 1,000 → 운영 10,000"],
  ]
));

children.push(P("6개 API 모두 운영키 승인이 완료되면 P1의 후반부(개발 환경 셋업)와 병행하여 P2(PoC) 단계로 즉시 진입한다."));

const doc = new Document({
  creator: "라피오자", title: "공공데이터포털 나라장터 6개 API 활용신청 실무 가이드",
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
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 480, hanging: 240 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 480, hanging: 240 } } } }] },
      { reference: "checks",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "☐", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 480, hanging: 280 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } },
    },
    headers: { default: new Header({
      children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "GovProcu — 공공데이터포털 6개 API 활용신청 가이드", font: FONT, size: 18, color: "808080" })],
      })],
    }) },
    footers: { default: new Footer({
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "- ", font: FONT, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" }),
          new TextRun({ text: " -", font: FONT, size: 18, color: "808080" }),
        ],
      })],
    }) },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/sessions/determined-dazzling-mendel/mnt/GovProcu/docs/공공데이터포털_나라장터_API_활용신청_가이드.docx", buf);
  console.log("OK");
});
