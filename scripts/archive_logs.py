"""로그 archive — 90일 이상 누적된 로그/감사를 압축·이관.

NEXT7-T8 운영 트랙.

기능:
1. logs/*.md 의 90일+ 부분을 logs/archive/YYYYMM.md.gz 로 이전
2. audit_log 테이블의 90일+ row 를 runtime/archive/audit_YYYYMM.jsonl.gz 로 export 후 삭제
3. 분기별(매 3개월) 자동 실행 권장 — Windows Task Scheduler 또는 cron

사용법:
    python scripts/archive_logs.py --days 90 --dry-run
    python scripts/archive_logs.py --days 90              # 실제 실행
    python scripts/archive_logs.py --audit-only --days 90 # audit만

환경:
    DB_PATH (자동) — runtime/govprocu.db
    LOG_DIR (자동) — logs/
"""
from __future__ import annotations
import argparse
import asyncio
import gzip
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트 import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def archive_logs_files(days: int, dry_run: bool) -> dict:
    """logs/*.md 파일에서 90일+ 부분을 별도 압축 파일로 이전.

    현재 정책: 파일 전체를 archive 대상이 아닌, 단일 markdown 파일을 통째로
    분기별 archive 폴더로 이동. Append-only 로그 특성상 파일이 매월·매분기 회전됨.
    여기서는 mtime 기준으로 N일 이상 된 파일을 통째 archive.
    """
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    archive_dir = log_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    threshold = datetime.now() - timedelta(days=days)
    moved = []

    for md in log_dir.glob("*.md"):
        if md.name in ("WORK-LOG.md", "PROMPTS-LOG.md", "TERMINAL-LOG.md"):
            # 활성 로그는 통째 archive 하지 않음 (헤더 split 정책 별도 검토)
            continue
        mtime = datetime.fromtimestamp(md.stat().st_mtime)
        if mtime >= threshold:
            continue

        target = archive_dir / f"{md.stem}_{mtime.strftime('%Y%m')}.md.gz"
        if not dry_run:
            with md.open("rb") as src, gzip.open(target, "wb") as dst:
                dst.write(src.read())
            md.unlink()
        moved.append({"src": str(md), "dst": str(target), "mtime": mtime.isoformat()})

    return {
        "scanned_dir": str(log_dir),
        "archive_dir": str(archive_dir),
        "threshold": threshold.isoformat(),
        "moved_count": len(moved),
        "moved": moved,
        "dry_run": dry_run,
    }


async def archive_audit_log(days: int, dry_run: bool) -> dict:
    """audit_log 테이블의 N일+ row를 JSONL.gz 로 export 후 삭제."""
    import aiosqlite

    from app.storage.db import DB_PATH

    if not Path(DB_PATH).exists():
        return {"error": "DB not found", "db_path": str(DB_PATH)}

    archive_dir = Path(__file__).resolve().parent.parent / "runtime" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    threshold = datetime.now() - timedelta(days=days)
    threshold_iso = threshold.strftime("%Y-%m-%d %H:%M:%S")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # 1. count
        cur = await db.execute(
            "SELECT COUNT(*) AS c FROM audit_log WHERE ts < ?",
            (threshold_iso,),
        )
        row = await cur.fetchone()
        count = (row["c"] if row else 0) or 0
        if count == 0:
            return {
                "threshold": threshold_iso,
                "rows_to_archive": 0,
                "dry_run": dry_run,
            }

        if dry_run:
            return {
                "threshold": threshold_iso,
                "rows_to_archive": count,
                "dry_run": True,
                "note": "would export + delete",
            }

        # 2. export
        cur = await db.execute(
            "SELECT * FROM audit_log WHERE ts < ? ORDER BY id",
            (threshold_iso,),
        )
        rows = [dict(r) for r in await cur.fetchall()]

        ym = threshold.strftime("%Y%m")
        fname = archive_dir / f"audit_until_{ym}.jsonl.gz"
        with gzip.open(fname, "wt", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        # 3. delete
        await db.execute("DELETE FROM audit_log WHERE ts < ?", (threshold_iso,))
        await db.commit()

        # VACUUM으로 파일 크기 회수 (옵션)
        await db.execute("VACUUM")
        await db.commit()

    return {
        "threshold": threshold_iso,
        "exported_rows": count,
        "archive_file": str(fname),
        "dry_run": False,
    }


async def amain(args) -> None:
    print(f"=== Archive logs (days >= {args.days}, dry_run={args.dry_run}) ===\n")

    if not args.audit_only:
        files_result = archive_logs_files(args.days, args.dry_run)
        print("[1] log files:")
        print(json.dumps(files_result, ensure_ascii=False, indent=2)[:1500])
        print()

    audit_result = await archive_audit_log(args.days, args.dry_run)
    print("[2] audit_log:")
    print(json.dumps(audit_result, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description="GovProcu logs/audit archive")
    p.add_argument("--days", type=int, default=90, help="N일 이상 archive (default 90)")
    p.add_argument("--dry-run", action="store_true", help="실제 변경 없이 시뮬레이션")
    p.add_argument("--audit-only", action="store_true", help="audit_log 만 archive")
    args = p.parse_args()
    asyncio.run(amain(args))


if __name__ == "__main__":
    main()
