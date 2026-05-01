# G2B API 직접 호출 테스트 (.env의 G2B_KEY_BID 사용)
# 실행: powershell -ExecutionPolicy Bypass -File scripts\test_g2b_call.ps1

$ErrorActionPreference = "Stop"
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

# .env에서 키 로드
$envPath = "C:\Users\User\GovProcu\.env"
if (-not (Test-Path $envPath)) {
    Write-Host "ERROR: .env 파일이 없습니다: $envPath" -ForegroundColor Red
    exit 1
}

$key = (Get-Content $envPath | Where-Object { $_ -match '^G2B_KEY_BID=' } | Select-Object -First 1) -replace '^G2B_KEY_BID=', ''
$key = $key.Trim().Trim('"').Trim("'")

if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "ERROR: G2B_KEY_BID 값이 .env에 없거나 비어있음" -ForegroundColor Red
    exit 1
}

$tail = $key.Substring($key.Length - 4)
Write-Host "키 마지막 4자리: $tail (길이 $($key.Length))" -ForegroundColor Cyan

# 호출 파라미터
$params = @{
    ServiceKey  = $key
    type        = "json"
    pageNo      = "1"
    numOfRows   = "20"
    inqryDiv    = "1"
    inqryBgnDt  = "202603200000"
    inqryEndDt  = "202604202359"
    bidNtceNm   = "정보화"
}

# URL 조립 (수동 인코딩)
$qs = ($params.GetEnumerator() | ForEach-Object {
    "$($_.Key)=$([System.Uri]::EscapeDataString($_.Value))"
}) -join "&"

# Encoding 키는 이미 인코딩된 상태이므로 ServiceKey만 원본 유지
$qs = $qs -replace [regex]::Escape("ServiceKey=$([System.Uri]::EscapeDataString($key))"), "ServiceKey=$key"

$url = "http://apis.data.go.kr/1230000/BidPublicInfoService05/getBidPblancListInfoServc?$qs"
Write-Host ""
Write-Host "URL (마스킹):" -ForegroundColor Gray
Write-Host ($url -replace "ServiceKey=$key", "ServiceKey=***$tail") -ForegroundColor DarkGray
Write-Host ""

try {
    $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 15
} catch {
    Write-Host "HTTP 오류: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "Body: $($reader.ReadToEnd())" -ForegroundColor DarkRed
    }
    exit 1
}

$header = $resp.response.header
$body = $resp.response.body
Write-Host "resultCode=$($header.resultCode) resultMsg=$($header.resultMsg)" -ForegroundColor Cyan

if ($header.resultCode -ne "00") {
    Write-Host "G2B 에러 응답:" -ForegroundColor Red
    $resp | ConvertTo-Json -Depth 5 | Write-Host
    exit 1
}

$items = @($body.items)
$total = $body.totalCount
Write-Host "전체 건수: $total" -ForegroundColor Green

# 국방 재정관리단 필터
$matched = @($items | Where-Object {
    ($_.ntceInsttNm -and $_.ntceInsttNm.Contains("국방") -and $_.ntceInsttNm.Contains("재정관리")) -or
    ($_.dminsttNm   -and $_.dminsttNm.Contains("국방")   -and $_.dminsttNm.Contains("재정관리"))
})

Write-Host "국방 재정관리단 매칭: $($matched.Count)건" -ForegroundColor Green
Write-Host ("=" * 80)

$show = if ($matched.Count -gt 0) { $matched | Select-Object -First 5 } else {
    Write-Host "  국방 재정관리단 매칭 0건. 키워드 '정보화' 용역 상위 5건 표시:" -ForegroundColor Yellow
    $items | Select-Object -First 5
}

$i = 0
foreach ($it in $show) {
    $i++
    Write-Host ""
    Write-Host "[$i] 공고번호 $($it.bidNtceNo)-$($it.bidNtceOrd)" -ForegroundColor White
    Write-Host "    제목: $($it.bidNtceNm)"
    Write-Host "    발주기관: $($it.ntceInsttNm) / 수요기관: $($it.dminsttNm)"
    Write-Host "    추정가격: $($it.presmptPrce) / 배정예산: $($it.asignBdgtAmt)"
    Write-Host "    공고일: $($it.bidNtceDt) / 마감: $($it.bidClseDt)"
    if ($it.bidNtceUrl) { Write-Host "    URL: $($it.bidNtceUrl)" }
}
