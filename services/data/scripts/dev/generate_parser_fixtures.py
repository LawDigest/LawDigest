"""파서 테스트 픽스처 생성 스크립트.

PDF를 파싱하여 결과를 JSON 픽스처 파일로 저장한다.
파서 코드가 변경될 때마다 재실행하여 픽스처를 갱신한다.

사용법:
    # 모든 대상 파싱
    python scripts/dev/generate_parser_fixtures.py

    # 특정 기관만
    python scripts/dev/generate_parser_fixtures.py --pollster 한국리서치
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))

from tqdm import tqdm  # noqa: E402

from lawdigest_data.polls.parser import PollResultParser  # noqa: E402

# ── 경로 ──────────────────────────────────────────────────────────────────────

# PDF는 main 프로젝트 경로에서 조회 (워크트리에는 output/ 없음)
_MAIN_DATA = Path("/home/ubuntu/project/Lawdigest/services/data")
_PDF_DIR = (
    (_MAIN_DATA if (_MAIN_DATA / "output" / "pdfs").exists() else _BASE)
    / "output" / "pdfs" / "제9회 전국동시지방선거" / "경기도 전체"
)
_FIXTURE_DIR = _BASE / "tests" / "polls" / "fixtures"
_REGISTRY = _BASE / "config" / "parser_registry.json"

# ── 파싱 대상 목록 ─────────────────────────────────────────────────────────────
# (pollster_hint, pdf_filename)

TARGETS = [
    # 조원씨앤아이
    ("조원씨앤아이", "더팩트_경기도 지선 여론조사 보고서_250930.pdf"),
    ("조원씨앤아이", "더팩트 경기교육신문_경기도 지선 여론조사 보고서_251027.pdf"),
    ("조원씨앤아이", "경기일보_경기 지선 여론조사 보고서_251201(1).pdf"),
    ("조원씨앤아이", "경기일보_경기 지선 여론조사 보고서_260105.pdf"),
    ("조원씨앤아이", "경기일보_경기 지선 여론조사 보고서_260202_수정.pdf"),
    ("조원씨앤아이", "경기일보_경기 지선 여론조사 보고서_260224.pdf"),
    ("조원씨앤아이", "프레시안_경기 지선 여론조사 보고서_260318_f.pdf"),
    # 데일리리서치
    ("(주)데일리리서치", "등록_경기도_결과분석_데일리리서치2510011.pdf"),
    # 리얼미터
    ("(주)리얼미터", "(리얼-오마이)결과표_경기도 지방선거 여론조사_최종.pdf"),
    ("(주)리얼미터", "2. (리얼미터)결과표_오마이뉴스 경기도 지방선거 및 현안 조사_최종.pdf"),
    # 한국리서치
    ("(주)한국리서치", "(경인일보)지방선거 경기도민 여론조사_결과표_2월 22일 보도용.pdf"),
    ("(주)한국리서치", "(경인일보)지방선거 경기도민 여론조사_결과표_2월 23일 보도용.pdf"),
    # 시그널앤펄스
    ("(주)시그널앤펄스", "보도용_경기도 여론조사 보고서_프레시안_260212.pdf"),
    ("(주)시그널앤펄스", "보도용_경기도 여론조사 보고서_프레시안_251230(수정).pdf"),
    ("(주)시그널앤펄스", "보도용_경기도 여론조사 보고서_서울의소리_251215.pdf"),
    # 윈지코리아컨설팅
    ("(주)윈지코리아컨설팅", "260305_공표용보고서_경기도_정치지형조사_v2.pdf"),
    ("(주)윈지코리아컨설팅", "250915_보고서_드림투데이(경기)_v2.pdf"),
]


def _fixture_path(pollster: str, fname: str) -> Path:
    """픽스처 파일 경로를 반환한다 (파일명 기반 슬러그)."""
    slug = Path(fname).stem.replace(" ", "_").replace("(", "").replace(")", "")
    slug = slug[:60]  # 파일명 길이 제한
    return _FIXTURE_DIR / f"{slug}.json"


def _generate_one(
    parser: PollResultParser,
    pollster: str,
    fname: str,
    force: bool = False,
) -> dict:
    """단일 PDF를 파싱하고 픽스처를 저장한다."""
    pdf_path = _PDF_DIR / fname
    fixture_path = _fixture_path(pollster, fname)

    if not pdf_path.exists():
        return {"status": "skip", "reason": "PDF 없음"}

    if fixture_path.exists() and not force:
        return {"status": "skip", "reason": "픽스처 이미 존재 (--force로 덮어쓰기)"}

    t0 = time.monotonic()
    try:
        results = parser.parse_pdf(pdf_path, pollster_hint=pollster)
    except Exception as e:
        return {"status": "error", "reason": str(e)}
    elapsed = time.monotonic() - t0

    fixture = {
        "pollster": pollster,
        "pdf_filename": fname,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "question_count": len(results),
        "questions": [dataclasses.asdict(r) for r in results],
    }

    _FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {"status": "ok", "questions": len(results), "elapsed": elapsed}


def main() -> None:
    ap = argparse.ArgumentParser(description="파서 테스트 픽스처 생성")
    ap.add_argument("--pollster", help="특정 기관명 키워드만 처리 (부분 일치)")
    ap.add_argument("--force", action="store_true", help="기존 픽스처 덮어쓰기")
    args = ap.parse_args()

    targets = TARGETS
    if args.pollster:
        targets = [(p, f) for p, f in TARGETS if args.pollster in p]
        if not targets:
            print(f"[오류] '{args.pollster}'에 해당하는 대상이 없습니다.")
            sys.exit(1)

    parser = PollResultParser(registry_path=_REGISTRY)
    ok = skip = err = 0
    started_at = time.monotonic()

    tqdm.write(f"픽스처 생성 시작 — {len(targets)}건 대상")

    with tqdm(total=len(targets), desc="픽스처 생성", unit="건", dynamic_ncols=True) as pbar:
        for idx, (pollster, fname) in enumerate(targets, start=1):
            pbar.set_postfix_str(f"{idx}/{len(targets)} {fname[:24]}")
            result = _generate_one(parser, pollster, fname, force=args.force)
            status = result["status"]

            if status == "ok":
                ok += 1
                tqdm.write(
                    f"  ✔ [{idx}/{len(targets)}] {result['questions']:>3}Q  {result['elapsed']:.1f}s  {fname[:55]}"
                )
            elif status == "skip":
                skip += 1
                tqdm.write(f"  - [{idx}/{len(targets)}] SKIP  {fname[:55]}  ({result['reason']})")
            else:
                err += 1
                tqdm.write(f"  ✘ [{idx}/{len(targets)}] ERR   {fname[:55]}  ({result['reason']})")

            elapsed_total = time.monotonic() - started_at
            avg_per_item = elapsed_total / idx
            remaining = max(len(targets) - idx, 0) * avg_per_item
            pbar.set_postfix_str(
                f"ok={ok} skip={skip} err={err} elapsed={elapsed_total:.1f}s eta={remaining:.1f}s"
            )
            pbar.update(1)

    total_elapsed = time.monotonic() - started_at
    tqdm.write(f"\n완료: 생성={ok}  스킵={skip}  오류={err}  총소요={total_elapsed:.1f}s")
    tqdm.write(f"픽스처 위치: {_FIXTURE_DIR}")


if __name__ == "__main__":
    main()
