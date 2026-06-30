"""Bill.category 백필 (무API).

위원회 매핑(경로 2) + 본회의/미상 내용 분류(경로 3, path A)로 `category IS NULL` 행을 채운다.
LLM 호출 없음. `unknown`(분류 불가)은 기록하지 않고 NULL로 남겨 추후 재처리 여지를 둔다.

사용:
  python -m scripts.backfill_bill_category --mode prod            # dry-run(집계만, 쓰기 없음)
  python -m scripts.backfill_bill_category --mode prod --execute  # 실제 UPDATE
  옵션: --limit N (대상 제한), --batch-size N (executemany 묶음)

설계·검증: output/tab-prototypes/FIELD_TAXONOMY.md (§4, §5).
"""
from __future__ import annotations

import argparse

from lawdigest_ai.db import get_bill_table_columns, get_db_connection
from lawdigest_ai.processor.category_classifier import classify_bill
from lawdigest_ai.processor.category_taxonomy import CODE_TO_LABEL, UNKNOWN_CODE


def run(*, mode: str, execute: bool, limit: int | None, batch_size: int) -> int:
    if "category" not in get_bill_table_columns(mode=mode):
        raise SystemExit("Bill.category 컬럼이 없습니다. 마이그레이션(20260630_add_bill_category)을 먼저 적용하세요.")

    conn = get_db_connection(mode=mode)
    try:
        select_sql = (
            "SELECT bill_id, committee, bill_name, brief_summary "
            "FROM Bill WHERE category IS NULL"
        )
        if limit:
            select_sql += f" LIMIT {int(limit)}"
        with conn.cursor() as cur:
            cur.execute(select_sql)
            rows = cur.fetchall()

        dist: dict[str, int] = {}
        updates: list[tuple[str, str]] = []
        for row in rows:
            code = classify_bill(row["committee"], row["bill_name"], row.get("brief_summary"))
            dist[code] = dist.get(code, 0) + 1
            if code != UNKNOWN_CODE:
                updates.append((code, row["bill_id"]))

        total = len(rows)
        classified = len(updates)
        unknown = dist.get(UNKNOWN_CODE, 0)
        print(f"[backfill_bill_category] mode={mode} execute={execute}")
        print(f"대상(category IS NULL): {total:,}")
        if total:
            print(f"분류 성공: {classified:,} ({classified / total * 100:.2f}%)   "
                  f"미분류(NULL 유지): {unknown:,} ({unknown / total * 100:.2f}%)")
        for code, count in sorted(dist.items(), key=lambda kv: -kv[1]):
            label = CODE_TO_LABEL.get(code, code)
            print(f"  {label:14s} {count:7,d}")

        if not execute:
            print("\n[dry-run] 쓰기 없음. 실제 반영하려면 --execute 를 붙이세요.")
            return classified

        updated = 0
        with conn.cursor() as cur:
            for start in range(0, len(updates), batch_size):
                chunk = updates[start:start + batch_size]
                updated += cur.executemany(
                    "UPDATE Bill SET category=%s WHERE bill_id=%s AND category IS NULL",
                    chunk,
                )
        conn.commit()
        print(f"\n[execute] UPDATE 완료: {updated:,} 행")
        return updated
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bill.category 백필 (무API)")
    parser.add_argument("--mode", default="test", choices=["test", "prod"])
    parser.add_argument("--execute", action="store_true", help="실제 UPDATE 수행(기본은 dry-run)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()
    run(mode=args.mode, execute=args.execute, limit=args.limit, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
