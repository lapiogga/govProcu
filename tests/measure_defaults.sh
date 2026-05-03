#!/usr/bin/env bash
# 각 페이지의 후보 날짜 범위별 라이브 측정 (응답시간 + 결과수)
# 사용자 N42-2 지시: 적정 default 결정용 perceived perf 측정
#
# 사용법: bash measure_defaults.sh > measure_defaults.log

set -u
BASE="http://localhost:3020"
TODAY=20260503

# 후보 from 일자 (오늘로부터 -N일)
declare -A FROM
FROM[D7]=20260426
FROM[D14]=20260419
FROM[D30]=20260403
FROM[D60]=20260304
FROM[D90]=20260202
FROM[D180]=20251104
FROM[D365]=20250503

measure() {
  local label="$1"
  local url="$2"
  local start end ms size
  start=$(date +%s%3N)
  size=$(curl -s -o /tmp/_meas_body.html -w "%{http_code}|%{size_download}" --max-time 120 "$url")
  end=$(date +%s%3N)
  ms=$((end - start))
  # 응답 안에 행 수 단서 추출 (서버 컴포넌트 텍스트에서 "총 N건" 패턴)
  local total=""
  total=$(grep -oE '총 [0-9,]+건' /tmp/_meas_body.html | head -1 | tr -d '총건 ' | tr -d ',')
  echo "${label}|${ms}|${size}|${total:-?}"
}

echo "=== /bids 키워드 LIKE — 다양한 날짜 범위 ==="
echo "label|ms|bytes|total_count"
for K in D7 D14 D30 D60 D90; do
  measure "/bids?q=정보화&from=${FROM[$K]}&to=${TODAY} ($K)" "${BASE}/bids?q=%EC%A0%95%EB%B3%B4%ED%99%94&from=${FROM[$K]}&to=${TODAY}"
done

echo
echo "=== /bids 업종 용역 (no keyword) ==="
for K in D7 D14 D30; do
  measure "/bids?type=용역&from=${FROM[$K]}&to=${TODAY} ($K)" "${BASE}/bids?type=%EC%9A%A9%EC%97%AD&from=${FROM[$K]}&to=${TODAY}"
done

echo
echo "=== /vendors LIKE — 다양한 날짜 범위 ==="
for K in D30 D60 D90 D180; do
  measure "/vendors?name=디지털&from=${FROM[$K]}&to=${TODAY} ($K)" "${BASE}/vendors?name=%EB%94%94%EC%A7%80%ED%84%B8&from=${FROM[$K]}&to=${TODAY}"
done

echo
echo "=== /vendors/{bizNo} 단건 프로필 (default 적용) ==="
measure "/vendors/1058705373 (default)" "${BASE}/vendors/1058705373"

echo
echo "=== /agencies 다양한 범위 ==="
for K in D90 D180 D365; do
  measure "/agencies?name=한국수자원공사&from=${FROM[$K]}&to=${TODAY} ($K)" "${BASE}/agencies?name=%ED%95%9C%EA%B5%AD%EC%88%98%EC%9E%90%EC%9B%90%EA%B3%B5%EC%82%AC&from=${FROM[$K]}&to=${TODAY}"
done

echo
echo "=== /external/kwater 단일 월 ==="
measure "/external/kwater?dt=202205&biz=용역" "${BASE}/external/kwater?dt=202205&biz=%EC%9A%A9%EC%97%AD"
measure "/external/kwater?dt=202604&biz=용역 (default)" "${BASE}/external/kwater?dt=202604&biz=%EC%9A%A9%EC%97%AD"

echo "=== DONE ==="
