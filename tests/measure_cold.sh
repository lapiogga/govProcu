#!/usr/bin/env bash
# Cold 측정 — 각 호출 사이 redis FLUSHALL 로 캐시 무효화
# 1차 호출 perceived 시간을 정확히 측정
set -u
BASE="http://localhost:3020"
TODAY=20260503

flush() {
  docker exec govprocu-redis redis-cli FLUSHALL > /dev/null 2>&1
}

measure() {
  local label="$1"
  local url="$2"
  flush
  local start end ms total
  start=$(date +%s%3N)
  curl -s --max-time 180 "$url" > /tmp/_cold_body.html
  end=$(date +%s%3N)
  ms=$((end - start))
  total=$(grep -oE '총 [0-9,]+건' /tmp/_cold_body.html | head -1 | sed 's/[^0-9,]//g' | tr -d ',')
  # /bids 의 returned_count "반환 N" + "결과 없음 (N건)" 모두 처리
  local nores=$(grep -oE '결과 없음 \([0-9,]+건\)' /tmp/_cold_body.html | head -1 | sed 's/[^0-9,]//g' | tr -d ',')
  local cand=$(grep -oE '후보 [^"<]*업체 [0-9]+개' /tmp/_cold_body.html | head -1 | sed 's/[^0-9]//g')
  local kw=$(grep -oE '"총 [0-9,]+건' /tmp/_cold_body.html | head -1 | sed 's/[^0-9,]//g' | tr -d ',')
  echo "${label}|${ms}ms|total=${total:-${nores:-?}}|cand=${cand:-?}"
}

echo "==== /bids 키워드 LIKE (cold) ===="
measure "D7  q=정보화 4/26-5/3"   "${BASE}/bids?q=%EC%A0%95%EB%B3%B4%ED%99%94&from=20260426&to=${TODAY}"
measure "D14 q=AI 4/19-5/3"        "${BASE}/bids?q=AI&from=20260419&to=${TODAY}"
measure "D30 q=한의약 4/3-5/3"     "${BASE}/bids?q=%ED%95%9C%EC%9D%98%EC%95%BD&from=20260403&to=${TODAY}"
measure "D60 q=클라우드 3/4-5/3"   "${BASE}/bids?q=%ED%81%B4%EB%9D%BC%EC%9A%B0%EB%93%9C&from=20260304&to=${TODAY}"

echo
echo "==== /bids 업종 단독 (cold) ===="
measure "D14 type=용역"             "${BASE}/bids?type=%EC%9A%A9%EC%97%AD&from=20260419&to=${TODAY}"
measure "D30 type=공사"             "${BASE}/bids?type=%EA%B3%B5%EC%82%AC&from=20260403&to=${TODAY}"

echo
echo "==== /vendors LIKE (cold) — 시간 비교 ===="
measure "D30 name=디지털"            "${BASE}/vendors?name=%EB%94%94%EC%A7%80%ED%84%B8&from=20260403&to=${TODAY}"
measure "D60 name=솔루션"            "${BASE}/vendors?name=%EC%86%94%EB%A3%A8%EC%85%98&from=20260304&to=${TODAY}"
measure "D90 name=시스템"            "${BASE}/vendors?name=%EC%8B%9C%EC%8A%A4%ED%85%9C&from=20260202&to=${TODAY}"

echo
echo "==== /vendors/{bizNo} 단건 (cold) — Y1 chunk ===="
measure "/vendors/1058705373 (default)"           "${BASE}/vendors/1058705373"
measure "/vendors/1131171595"                     "${BASE}/vendors/1131171595"

echo
echo "==== /agencies (cold) ===="
measure "D90 한국수자원공사"        "${BASE}/agencies?name=%ED%95%9C%EA%B5%AD%EC%88%98%EC%9E%90%EC%9B%90%EA%B3%B5%EC%82%AC&from=20260202&to=${TODAY}"
measure "D180 한국전력공사"          "${BASE}/agencies?name=%ED%95%9C%EA%B5%AD%EC%A0%84%EB%A0%A5%EA%B3%B5%EC%82%AC&from=20251104&to=${TODAY}"
measure "D365 과학기술정보통신부"    "${BASE}/agencies?name=%EA%B3%BC%ED%95%99%EA%B8%B0%EC%88%A0%EC%A0%95%EB%B3%B4%ED%86%B5%EC%8B%A0%EB%B6%80&from=20250503&to=${TODAY}"

echo
echo "==== /external/kwater (cold) ===="
measure "dt=202205 용역" "${BASE}/external/kwater?dt=202205&biz=%EC%9A%A9%EC%97%AD"
measure "dt=202604 용역 default" "${BASE}/external/kwater?dt=202604&biz=%EC%9A%A9%EC%97%AD"

echo "==== DONE ===="
