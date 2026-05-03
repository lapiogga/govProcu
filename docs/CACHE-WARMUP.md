# Cache Warmup ETL 운영 가이드

> 사용자 첫 호출도 **cache hit (0.5초)** 보장.
> v27.1 (636cb6f) 도입. 5초 SLA 마지막 단계.

## 배경

- `app/core/cache.py` Redis 기반 (redis.asyncio)
- v23.5/v23.7로 핵심 11개 MCP 도구에 `@cache_result(30분 TTL)` 적용
- cache miss 시 5~20초 / cache hit 시 0.5초

**문제**: 첫 사용자 또는 30분 미사용 후 첫 호출 = 항상 cache miss → 5~20초.

**해결**: scheduled background warmup이 인기 검색을 30분마다 호출 → Redis cache 항상 hot.

## 단일 실행 (수동 검증)

```powershell
cd C:\Users\User\GovProcu
python scripts/etl_warmup.py
```

예상 출력:
```
=== ETL warmup start: 2026-05-03T23:55:00 ===
  range: 20260403~20260503 (30일)
  bids: kw='정보화' biz=None
  bids: kw='정보화' biz='용역'
  ...
  awards: inst='국방부' biz='용역'
  ...
  history: inst='국방부'
  ...
OK warmup 완료: bids=16, awards=12, history=4 / elapsed=120.5s
```

(첫 실행은 Redis 채우는 데 1~3분. 그 다음부턴 모두 cache hit으로 5초 내.)

## 정기 등록

### Windows Task Scheduler (PowerShell 관리자)

```powershell
$action = New-ScheduledTaskAction -Execute 'python.exe' `
  -Argument 'C:\Users\User\GovProcu\scripts\etl_warmup.py' `
  -WorkingDirectory 'C:\Users\User\GovProcu'

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes 30) `
  -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask -TaskName 'GovProcu Cache Warmup' `
  -Action $action -Trigger $trigger `
  -RunLevel Highest -Force
```

확인:
```powershell
Get-ScheduledTask -TaskName 'GovProcu Cache Warmup'
Get-ScheduledTaskInfo -TaskName 'GovProcu Cache Warmup'
```

### Linux cron

```bash
# crontab -e
*/30 * * * * cd /path/to/GovProcu && python scripts/etl_warmup.py >> logs/warmup.log 2>&1
```

### macOS launchd

`~/Library/LaunchAgents/com.govprocu.warmup.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.govprocu.warmup</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/path/to/GovProcu/scripts/etl_warmup.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/path/to/GovProcu</string>
  <key>StartInterval</key>
  <integer>1800</integer>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.govprocu.warmup.plist
```

## 조정

### POPULAR_* 수정

`scripts/etl_warmup.py`:
```python
POPULAR_KEYWORDS = ["정보화", "구축사업", "유지보수", "용역"]
POPULAR_AGENCIES = ["국방부", "경찰청", "조달청", "한국수자원공사"]
```

운영 환경에 맞게 조정. 변경 후 재실행 필요 (cache key가 args 기반 hash).

### 빈도

- 30분 default — `cache_ttl_short=1800`과 정합
- 더 자주 (10분 등) 가능 — backend G2B rate-limit 주의

### 효과 측정

```powershell
# Redis CLI
redis-cli -h localhost -p 6379
> KEYS bid_v24:*
> KEYS award_list_v24:*
> TTL bid_v24:search_bid_notices:abc123
```

키 개수 = cache hit 가능 검색 수.

## 후속 (별도 sprint)

- 사용자 검색 빈도 자동 학습 → POPULAR_* 자동 갱신
- 사용자별 personal warmup (즐겨찾기 + 최근 검색 기반)
- Redis 영속화 (volume mount) — 재시작 시 cache 유지
