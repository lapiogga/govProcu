"""GraphRAG — 자연어 질의 → Cypher 자동 생성 → 실행 → 자연어 응답.

NEXT7-T7 (Phase R4): R3 graph 도구 위에 LLM 자동 변환층.

흐름:
1. 사용자 자연어 질문 ("가장 활발한 낙찰업체는?")
2. Anthropic Claude → schema + 질문 → Cypher 생성
3. read-only 검증 (WRITE/CREATE/MERGE/DELETE/SET 거부)
4. Neo4j 실행 (limit 100 강제)
5. 결과 + 원 질문 → Claude → 자연어 요약

환경변수:
    ANTHROPIC_API_KEY  — 필수
    NEO4J_URI          — 필수 (graph.py 와 동일)
"""
from __future__ import annotations
import os
import re

# graph.py 의 헬퍼 재사용
from app.tools.graph import _neo4j_available, _get_driver


GRAPH_SCHEMA = """
GovProcu Neo4j 그래프 스키마

노드:
  (:Agency {inst_code, inst_name})           — 발주기관
  (:BidNotice {bid_notice_no, bid_ord, title, base_amount, biz_type, publish_date})
                                              — 입찰공고
  (:Vendor {biz_no, vendor_name})             — 응찰·낙찰업체
  (:Contract {contract_no, signed_date})      — 계약

관계 (방향):
  (BidNotice)-[:ISSUED_BY]->(Agency)
  (BidNotice)-[:AWARDED_TO {amount, rate}]->(Vendor)        — 낙찰
  (Vendor)-[:PARTICIPATED_IN {amount}]->(BidNotice)         — 응찰 (참여)
  (Contract)-[:SIGNED_WITH]->(Vendor)
  (Contract)-[:CONTRACTED_AS]->(BidNotice)

관례:
- biz_no 는 하이픈 없는 10자리 숫자 (예: '1234567890')
- inst_name 은 한글 공식명 (예: '국방재정관리단')
- bid_notice_no + bid_ord 가 공고 단위 unique key
- 모든 금액은 원 (KRW)
""".strip()


_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(CREATE|MERGE|DELETE|SET|REMOVE|DROP|DETACH|FOREACH|LOAD\s+CSV|"
    r"CALL\s+db\.|CALL\s+dbms\.|CALL\s+apoc\.create|CALL\s+apoc\.merge)\b",
    re.IGNORECASE,
)


def is_read_only_cypher(cypher: str) -> tuple[bool, str]:
    """Cypher 가 read-only 인지 검증."""
    if _FORBIDDEN_KEYWORDS.search(cypher):
        match = _FORBIDDEN_KEYWORDS.search(cypher)
        return False, f"write keyword detected: {match.group(0)}"
    if "MATCH" not in cypher.upper() and "RETURN" not in cypher.upper():
        return False, "Cypher must contain MATCH/RETURN"
    return True, ""


def enforce_limit(cypher: str, limit: int = 100) -> str:
    """LIMIT 절이 없으면 강제 추가."""
    if re.search(r"\bLIMIT\s+\d+\b", cypher, re.IGNORECASE):
        return cypher
    return f"{cypher.rstrip(';').rstrip()}\nLIMIT {limit}"


async def _generate_cypher_with_claude(
    natural_query: str,
    api_key: str,
) -> dict:
    """Claude → Cypher 합성. tool_use 없이 단순 generation 사용."""
    try:
        import anthropic
    except ImportError:
        return {"error": "pip install anthropic"}

    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""당신은 GovProcu (한국 정부 입찰 시스템) Neo4j 데이터베이스의 Cypher 전문가입니다.

{GRAPH_SCHEMA}

사용자 질문을 한 개의 read-only Cypher 쿼리로 변환하세요.
규칙:
- WRITE 절(CREATE/MERGE/DELETE/SET/REMOVE) 사용 금지 (read-only).
- LIMIT 100 이내.
- 결과 컬럼명을 의미 있게 alias.
- 응답은 Cypher 본문만, 코드블록·설명 없이.

사용자 질문:
{natural_query}

Cypher:"""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",  # 빠른 모델 (cf. claudeMd 환경)
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        block.text for block in msg.content if hasattr(block, "text")
    ).strip()
    # 코드블록 제거 (```cypher ... ```)
    text = re.sub(r"^```\w*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()
    return {"cypher": text}


async def _summarize_results_with_claude(
    natural_query: str,
    cypher: str,
    rows: list[dict],
    api_key: str,
) -> str:
    """결과 → 자연어 요약."""
    try:
        import anthropic
    except ImportError:
        return f"({len(rows)}건 — anthropic 미설치로 요약 생략)"

    client = anthropic.Anthropic(api_key=api_key)
    sample = rows[:20]
    prompt = f"""사용자가 다음 질문을 했습니다:
{natural_query}

실행된 Cypher:
{cypher}

결과 (상위 {len(sample)}건):
{sample}

위 결과를 한국어로 2~5문장으로 명확히 요약하세요. 핵심 수치·이름을 포함하고, 원 질문에 직접 답하세요."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in msg.content if hasattr(block, "text")
    ).strip()


async def graph_natural_query(query: str, max_rows: int = 100) -> dict:
    """자연어 → Cypher → 결과 + 자연어 요약.

    Args:
        query: 한국어 자연어 질문 (예: "가장 많은 낙찰을 받은 상위 5개 업체는?")
        max_rows: 결과 행 한도

    Returns:
        {
          "status": "ok|error|neo4j_not_configured|...",
          "natural_query": str,
          "cypher": str,
          "rows": [...],
          "summary": str,
        }
    """
    ok, err = _neo4j_available()
    if not ok:
        return {"status": "neo4j_not_configured", "note": err}

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "status": "anthropic_not_configured",
            "note": "ANTHROPIC_API_KEY 환경변수 미설정",
        }

    # 1. Cypher 합성
    gen = await _generate_cypher_with_claude(query, api_key)
    if "error" in gen:
        return {"status": "llm_error", "error": gen["error"]}
    cypher = gen["cypher"]

    # 2. read-only 검증
    safe, reason = is_read_only_cypher(cypher)
    if not safe:
        return {
            "status": "rejected_unsafe_cypher",
            "natural_query": query,
            "cypher": cypher,
            "reason": reason,
        }

    cypher = enforce_limit(cypher, max_rows)

    # 3. 실행
    try:
        driver = _get_driver()
        with driver.session() as session:
            rows = session.run(cypher).data()
        driver.close()
    except Exception as exc:
        return {
            "status": "cypher_execution_error",
            "natural_query": query,
            "cypher": cypher,
            "error": str(exc)[:300],
        }

    # 4. 자연어 요약
    summary = await _summarize_results_with_claude(query, cypher, rows, api_key)

    return {
        "status": "ok",
        "natural_query": query,
        "cypher": cypher,
        "row_count": len(rows),
        "rows": rows[:max_rows],
        "summary": summary,
    }
