# Phase 24 — WORK-LOG (시계열)

## 2026-05-03 (일)

| 시각 (KST) | 행위자 | 작업 | 결과 / 산출물 |
|-----------|--------|------|---------------|
| 22:42 | lead | Phase 24 신설 | `PLAN.md` + 본 `WORK-LOG.md`. F3 매칭 강화 자동 진행 |
| 22:43 | lead | v24.1 적용 | (1) `app/tools/award.py`: `inst_name not in inst` → 토큰 기반 매칭 (`all(t in inst for t in inst_name.split())`). cache prefix `award_list` → `award_list_v24` (cache 무효화). (2) `app/tools/bid.py`: `inp.inst_name not in inst` → 동일 토큰 매칭. cache prefix `bid` → `bid_v24`. sanity check 5/5 케이스 OK |
| 22:50 | user | 발화 #14 (현재 시간 timezone 질의) | 답변: KST UTC+9 / Korea Standard Time |
| 22:54 | lead | v24.1 commit (715a5d1) | atomic |
| 22:56 | lead | v24.2 적용 | (1) `app/tools/award.py` `search_awards`: `inst_sample_counts` dict 수집 (raw inst 표기, 필터 통과 무관). 응답에 `sample_inst_names` (상위 5개) 추가. (2) `app/tools/analytics.py` `analyze_agency_price_pattern`: 매칭 0건 시 `note`에 sample 첨부 + `sample_inst_names` 응답 동봉. 사용자가 정확 표기 학습 가능. import sanity check OK |
| 22:58 | lead | v24.2 commit (5001a99) | atomic |
| 23:00 | lead | v24.3 적용 | `frontend/src/app/agencies/page.tsx` PriceCard 매칭 0건 분기에 `sample_inst_names` 시각 카드 추가 (warning border, 출현 빈도 안내, 클릭 가이드). frontend rebuild 후 사용자에게 학습 강조 |
