# TERMINAL-LOG

> 본 파일은 본 프로젝트에서 실행된 모든 터미널 명령과 그 결과를 시계열로 기록한다.
> 시간 기준: KST (Asia/Seoul, UTC+9)

---

## 2026-04-29 (수)

### [10:47:30 KST] `date "+%Y-%m-%d %H:%M:%S %z (%Z)"` (현재시각 확인)
```
2026-04-29 01:48:18 +0000 (UTC)   # = 2026-04-29 10:48:18 KST
```

### [10:47:35 KST] `cd outputs && node build_plan.js` (1차 시도)
```
Error: Cannot find module 'docx'
... (Node.js v22.22.0, MODULE_NOT_FOUND)
```
결과: 실패 — docx 패키지 미설치. 후속 작업으로 npm install 진행.

### [10:47:40 KST] `npm install docx`
```
added 22 packages in 6s
1 package is looking for funding
```
결과: 성공.

### [10:47:50 KST] `cd outputs && node build_plan.js && ls -la *.docx`
```
OK
-rwx------ 1 ... 24611 Apr 29 01:47 나라장터_MCP_서버_구축_계획서.docx
```
결과: 성공 — 24,611 bytes 문서 생성.

### [10:48:05 KST] `python3 scripts/office/validate.py 나라장터_MCP_서버_구축_계획서.docx`
```
Paragraphs: 0 → 421 (+421)
All validations PASSED!
```
결과: 검증 통과 — 421개 문단 정상.

### [11:05:00 KST] `mkdir -p docs logs scripts && cp ... GovProcu/`
```
(생략 — outputs의 4개 파일을 GovProcu/{docs,logs,scripts}로 복사)
```
결과: 파일 이동 완료. README.md, .gitignore도 신규 생성.

### [11:10:30 KST] `git init && git config ...` (마운트 위에서 시도)
```
fatal: bad config line 1 in file /sessions/.../GovProcu/.git/config
warning: unable to unlink '.git/config.lock': Operation not permitted
```
결과: **실패** — Cowork 마운트가 git 내부 파일 락(lock)·삭제 연산을 거부.

### [11:14:00 KST] /tmp 워크어라운드: `cp -r ... /tmp/GovProcu && git init -b main`
```
Initialized empty Git repository in /tmp/GovProcu/.git/
```
결과: 성공 — 정상 Linux 파일시스템에서는 git init 작동.

### [11:15:30 KST] `git add -A && git status --short`
```
A  .gitignore
A  README.md
A  docs/나라장터_MCP_서버_구축_계획서.docx
A  logs/TERMINAL-LOG.md
A  logs/WORK-LOG.md
A  scripts/build_plan.js
```
결과: 6개 파일 스테이징.

### [11:17:00 KST] `git commit -m "feat(plan): ..."`
```
[main (root-commit) 115b57f] feat(plan): 나라장터 MCP 서버 구축 계획서 v1.0 ...
 6 files changed, 716 insertions(+)
```
결과: 첫 커밋 생성 (115b57f).

### [11:19:00 KST] `git push -u origin main`
```
fatal: could not read Username for 'https://github.com': No such device or address
```
결과: **실패** — GitHub 인증 정보 미제공. PAT 또는 사용자 수동 push 필요.

### [11:30:00 KST] (사용자 PowerShell) `powershell -ExecutionPolicy Bypass -File scripts\setup-git.ps1`
```
위치 C:\Users\User\GovProcu\scripts\setup-git.ps1:37 문자:12
+ Write-Host "???꾨즺! https://github.com/lapiogga/govProcu ?먯꽌 ?뺤씤 媛??  ...
+            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
문자열에 " 종결자가 없습니다.
```
결과: **실패** — Korean Windows PowerShell이 UTF-8 .ps1을 CP949로 해석하여 한글 깨짐 + 파서 오류.

### [11:37:00 KST] setup-git.ps1 재작성 (BOM + 영문 메시지)
```
--- first 3 bytes of setup-git.ps1 ---
00000000: efbb bf                                  ...   (UTF-8 BOM 확인)
```
결과: 스크립트 메시지 영문화, UTF-8 BOM 부여, chcp 65001/i18n 설정 추가. 커밋 메시지는 scripts/.commit-msg.txt에 분리(UTF-8). 사용자 재실행 대기.

---

## 자동 기록 정책
- 매 20분 주기로 누적 기록을 회수·요약하여 본 파일 말미에 추가한다.
- 모든 명령은 `[HH:MM:SS KST] $ <command>` 형식으로 시작한다.
- stdout/stderr 전체가 너무 길 경우 마지막 20줄로 요약 + `...` 표기.
