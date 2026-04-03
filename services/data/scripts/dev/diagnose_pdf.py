"""PDF 파서 진단 스크립트.

미개발 파서 대상 PDF를 분석하여 다음 정보를 제공한다:
  1. PDF 기본 정보 (페이지 수, 텍스트 추출 가능 여부)
  2. 기존 파서 전체 시도 → 파싱 성공 여부 및 결과 건수
  3. 텍스트/테이블 구조 요약 (첫 N 페이지)
  4. 특징 문자열 탐지 (기존 파서 프로브 패턴)
  5. 파서 추천 의견

사용법:
    # 미개발 기관 전체 진단
    python scripts/dev/diagnose_pdf.py

    # 특정 PDF만
    python scripts/dev/diagnose_pdf.py --pdf "결과분석_한길리서치1019.pdf"

    # 상세 텍스트 덤프 포함
    python scripts/dev/diagnose_pdf.py --pdf "결과분석_한길리서치1019.pdf" --dump-text

    # 페이지 수 제한 (기본 3)
    python scripts/dev/diagnose_pdf.py --pages 5
"""
from __future__ import annotations

import argparse
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))

_MAIN_DATA = Path("/home/ubuntu/project/Lawdigest/services/data")
_PDF_DIR = (
    (_MAIN_DATA if (_MAIN_DATA / "output" / "pdfs").exists() else _BASE)
    / "output" / "pdfs" / "gyeonggi_governor"
)
_REGISTRY = _BASE / "config" / "parser_registry.json"

# ── 진단 대상 (미개발 기관) ─────────────────────────────────────────────────────

TARGETS: List[Tuple[str, str]] = [
    ("(주)케이스탯리서치",  "(결과표) KBS 지방선거 여론조사 [03. 경기].pdf"),
    ("(주)케이스탯리서치",  "지방선거 관련 여론조사(경기)_한글통계표(12.31).pdf"),
    ("(주)윈지코리아컨설팅", "250915_보고서_드림투데이(경기)_v2.pdf"),
    ("(주)윈지코리아컨설팅", "260305_공표용보고서_경기도_정치지형조사_v2.pdf"),
    ("(주)여론조사꽃",      "결과표_20260211_여론조사꽃_경기지사 2000_CATI조사_v01.pdf"),
    ("(주)여론조사꽃",      "결과표_20260326_여론조사꽃_경기도지사 2000_CATI조사_v01.pdf"),
    ("(주)여론조사꽃",      "결과표_20260317_여론조사꽃_경기도지사 1000_ARS조사_v01.pdf"),
    ("넥스트리서치",        "(넥스트리서치_조사결과_등록_0319) 제9회 전국동시지방선거관련 경기지역 여론조사.pdf"),
    ("㈜에스티아이",        "통계표_에스티아이_경기도지사 선거 여론조사 0219.pdf"),
    ("입소스 주식회사",     "(통계표) SBS 2026 설 특집 여론조사_경기.pdf"),
    ("(주)한길리서치",      "결과분석_한길리서치1019.pdf"),
]

# 기존 파서에서 사용하는 특징 문자열
KNOWN_PROBES: Dict[str, str] = {
    "▣ 전체 ▣":          "_TableFormatParser / _KoreanResearchParser",
    "■ 전체 ■":          "_EmbrainPublicParser",
    "가중값적용사례수":    "_TableFormatParser",
    "조사 가중값":        "_RealMeterParser",
    "[표":               "_KoreanResearchParser / _SignalPulseParser",
    "[Q":                "_SignalPulseParser (구버전)",
    "N번)":              "_TextFormatParser",
}

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _hr(char: str = "─", width: int = 70) -> str:
    return char * width


def _truncate(text: str, max_lines: int = 20) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines]) + f"\n... (총 {len(lines)}줄, 처음 {max_lines}줄만 표시)"


def _try_all_parsers(pdf_path: Path) -> List[Dict]:
    """등록된 모든 파서 클래스로 파싱 시도 후 결과를 반환한다."""
    from lawdigest_data.polls.parser import (
        PollResultParser,
        _EmbrainPublicParser,
        _KoreanResearchParser,
        _RealMeterParser,
        _SignalPulseParser,
        _TableFormatParser,
        _TextFormatParser,
    )
    from lawdigest_data.polls.validation import validate_parse_results

    parser_classes = {
        "_TableFormatParser": _TableFormatParser,
        "_TextFormatParser": _TextFormatParser,
        "_RealMeterParser": _RealMeterParser,
        "_KoreanResearchParser": _KoreanResearchParser,
        "_SignalPulseParser": _SignalPulseParser,
        "_EmbrainPublicParser": _EmbrainPublicParser,
    }

    # pages_data 공통 추출 (한 번만)
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        pages_data = []
        full_text_parts = []
        for page in doc:
            finder = page.find_tables()
            tables = [t.extract() for t in finder.tables]
            page_text_outside = _extract_text_outside_tables_simple(page, finder)
            full_text = page.get_text()
            pages_data.append((page_text_outside, tables, full_text))
            full_text_parts.append(full_text)
        doc.close()
        full_text_combined = "\n".join(full_text_parts)
    except Exception as e:
        return [{"class": "ERROR", "error": str(e), "count": 0, "valid": False}]

    results = []
    for cls_name, cls in parser_classes.items():
        try:
            if cls_name == "_TextFormatParser":
                parsed = cls().parse(full_text_combined)
            else:
                parsed = cls().parse(pages_data)
            errors = validate_parse_results(parsed)
            valid_count = sum(1 for q_errs in errors.values() if not q_errs)
            results.append({
                "class": cls_name,
                "count": len(parsed),
                "valid_count": valid_count,
                "error_count": len([e for e in errors.values() if e]),
                "errors": errors,
                "exception": None,
            })
        except Exception as e:
            results.append({
                "class": cls_name,
                "count": 0,
                "valid_count": 0,
                "error_count": 0,
                "errors": {},
                "exception": str(e),
            })

    return results


def _extract_text_outside_tables_simple(page, finder) -> str:
    """테이블 외부 텍스트 추출 (진단용 간단 버전)."""
    table_bboxes = [t.bbox for t in finder.tables]

    def _in_table(wx0, wy0, wx1, wy1) -> bool:
        return any(
            wx0 >= tx0 - 3 and wy0 >= ty0 - 3 and wx1 <= tx1 + 3 and wy1 <= ty1 + 3
            for tx0, ty0, tx1, ty1 in table_bboxes
        )

    words = [w for w in page.get_text("words") if not _in_table(w[0], w[1], w[2], w[3])]
    words.sort(key=lambda w: (round(w[1]), w[0]))

    lines: List[str] = []
    current_y: Optional[float] = None
    line_words: List[str] = []
    for w in words:
        y = round(w[1])
        if current_y is None or abs(y - current_y) > 3:
            if line_words:
                lines.append(" ".join(line_words))
            current_y, line_words = y, [w[4]]
        else:
            line_words.append(w[4])
    if line_words:
        lines.append(" ".join(line_words))
    return "\n".join(lines)


def _analyze_structure(pdf_path: Path, max_pages: int = 3, dump_text: bool = False) -> Dict:
    """PDF 구조 분석: 페이지별 텍스트/테이블 요약."""
    try:
        import fitz
    except ImportError:
        return {"error": "pymupdf 미설치"}

    result: Dict = {
        "page_count": 0,
        "text_extractable": False,
        "cid_encoded": False,
        "pages": [],
        "full_text_sample": "",
        "probes_found": [],
    }

    try:
        doc = fitz.open(str(pdf_path))
        result["page_count"] = len(doc)
        all_text_parts = []

        for page_num, page in enumerate(doc):
            if page_num >= max_pages:
                break

            finder = page.find_tables()
            full_text = page.get_text()
            outside_text = _extract_text_outside_tables_simple(page, finder)
            tables = [t.extract() for t in finder.tables]

            # cid 인코딩 탐지
            cid_count = full_text.count("(cid:")
            if cid_count > 5:
                result["cid_encoded"] = True

            page_info: Dict = {
                "page_num": page_num + 1,
                "table_count": len(tables),
                "text_length": len(full_text),
                "outside_text_length": len(outside_text),
                "cid_count": cid_count,
                "table_shapes": [],
                "outside_text_sample": "",
                "table_samples": [],
            }

            # 테이블 형태 요약
            for i, tbl in enumerate(tables):
                if tbl:
                    rows = len(tbl)
                    cols = max(len(r) for r in tbl) if tbl else 0
                    page_info["table_shapes"].append(f"{rows}행×{cols}열")
                    if dump_text:
                        # 첫 5행만 샘플
                        sample_rows = tbl[:5]
                        page_info["table_samples"].append(sample_rows)

            if outside_text.strip():
                result["text_extractable"] = True
                page_info["outside_text_sample"] = _truncate(outside_text, 15) if not dump_text else outside_text

            result["pages"].append(page_info)
            all_text_parts.append(full_text)

        doc.close()

        full_text_all = "\n".join(all_text_parts)
        if full_text_all.strip():
            result["text_extractable"] = True

        # 특징 문자열 탐지 (전체 텍스트)
        try:
            doc2 = fitz.open(str(pdf_path))
            all_pages_text = "\n".join(page.get_text() for page in doc2)
            doc2.close()
            result["full_text_sample"] = _truncate(all_pages_text, 30) if not dump_text else all_pages_text
            for probe, hint in KNOWN_PROBES.items():
                if probe in all_pages_text:
                    result["probes_found"].append((probe, hint))
        except Exception:
            pass

    except Exception as e:
        result["error"] = str(e)

    return result


def _recommend_parser(struct: Dict, parser_results: List[Dict]) -> str:
    """분석 결과를 바탕으로 파서 추천 의견을 생성한다."""
    lines = []

    if struct.get("cid_encoded"):
        lines.append("⚠️  cid: 인코딩 감지 — 텍스트 추출 불가능. OCR 또는 이미지 기반 파싱 필요.")
        return "\n".join(lines)

    if not struct.get("text_extractable"):
        lines.append("⚠️  텍스트 추출 불가. 스캔 이미지 PDF일 가능성 있음.")
        return "\n".join(lines)

    # 기존 파서 시도 결과 중 최선
    best = max(
        (r for r in parser_results if r.get("exception") is None),
        key=lambda r: (r["valid_count"], r["count"]),
        default=None,
    )

    if best and best["count"] > 0:
        lines.append(
            f"✅ 기존 파서 재사용 가능 후보: {best['class']} "
            f"({best['count']}건 파싱, 유효 {best['valid_count']}건)"
        )
        if best["error_count"] > 0:
            lines.append(f"   단, {best['error_count']}건 검증 오류 있음 — 파서 조정 필요")
    else:
        lines.append("❌ 기존 파서 모두 실패 — 신규 파서 개발 필요")

    # 특징 프로브 기반 힌트
    if struct.get("probes_found"):
        for probe, hint in struct["probes_found"]:
            lines.append(f"   💡 '{probe}' 감지 → {hint} 참고")

    # 테이블 구조 힌트
    has_tables = any(p.get("table_count", 0) > 0 for p in struct.get("pages", []))
    if has_tables:
        lines.append("   📊 테이블 구조 있음 → _TableFormatParser 계열 적용 가능성")
    else:
        lines.append("   📝 테이블 없음 → _TextFormatParser 계열 검토")

    return "\n".join(lines) if lines else "분석 정보 부족"


# ── 출력 ──────────────────────────────────────────────────────────────────────

def diagnose_one(
    pollster: str,
    filename: str,
    max_pages: int = 3,
    dump_text: bool = False,
) -> None:
    pdf_path = _PDF_DIR / filename
    print(_hr("═"))
    print(f"📄 {filename}")
    print(f"   기관: {pollster}")
    print(_hr())

    if not pdf_path.exists():
        print(f"  ❌ 파일 없음: {pdf_path}")
        return

    # 1. 구조 분석
    print(f"\n[1] PDF 구조 분석 (최대 {max_pages} 페이지)")
    struct = _analyze_structure(pdf_path, max_pages=max_pages, dump_text=dump_text)

    if "error" in struct:
        print(f"  오류: {struct['error']}")
        return

    print(f"  총 페이지: {struct['page_count']}")
    print(f"  텍스트 추출 가능: {'✅' if struct['text_extractable'] else '❌'}")
    if struct["cid_encoded"]:
        print("  ⚠️  cid: 인코딩 감지됨")

    for p in struct["pages"]:
        cid_note = f" [cid:{p['cid_count']}개]" if p["cid_count"] > 0 else ""
        tbl_note = f"테이블 {p['table_count']}개 {p['table_shapes']}" if p["table_count"] > 0 else "테이블 없음"
        print(f"  p{p['page_num']}: {tbl_note}, 텍스트 {p['text_length']}자{cid_note}")

        if dump_text and p.get("outside_text_sample"):
            print("  --- 테이블 외부 텍스트 ---")
            for line in p["outside_text_sample"].splitlines():
                print(f"    {line}")

        if dump_text and p.get("table_samples"):
            for ti, tbl_sample in enumerate(p["table_samples"]):
                print(f"  --- 테이블 {ti+1} (첫 5행) ---")
                for row in tbl_sample:
                    # None → "" 치환 후 출력
                    cells = [str(c or "").strip()[:20] for c in row]
                    print(f"    {' | '.join(cells)}")

    # 특징 프로브
    if struct["probes_found"]:
        print(f"\n[2] 특징 문자열 탐지")
        for probe, hint in struct["probes_found"]:
            print(f"  ✓ '{probe}' → {hint}")
    else:
        print(f"\n[2] 특징 문자열: 기존 패턴 없음")

    # 2. 파서 전체 시도
    print(f"\n[3] 기존 파서 전체 시도")
    try:
        parser_results = _try_all_parsers(pdf_path)
        for r in parser_results:
            if r.get("exception"):
                print(f"  {r['class']:30s} → 예외: {r['exception'][:60]}")
            elif r["count"] == 0:
                print(f"  {r['class']:30s} → 0건 (파싱 실패)")
            else:
                status = "✅" if r["valid_count"] == r["count"] else "🔶"
                print(
                    f"  {r['class']:30s} → {status} {r['count']}건 파싱 "
                    f"(유효:{r['valid_count']}, 오류:{r['error_count']})"
                )
                if r["error_count"] > 0 and dump_text:
                    for q_key, errs in r["errors"].items():
                        if errs:
                            print(f"    [{q_key}] {', '.join(errs)}")
    except Exception:
        print("  파서 시도 중 오류:")
        traceback.print_exc()
        parser_results = []

    # 3. 텍스트 샘플 (dump_text 없을 때도 간단히)
    if not dump_text and struct.get("full_text_sample"):
        print(f"\n[4] 전문 텍스트 샘플 (첫 30줄)")
        sample = _truncate(struct["full_text_sample"], 30)
        for line in sample.splitlines():
            print(f"  {line}")

    # 4. 추천
    print(f"\n[5] 파서 추천")
    rec = _recommend_parser(struct, parser_results if "parser_results" in dir() else [])
    for line in rec.splitlines():
        print(f"  {line}")

    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="PDF 파서 진단 스크립트")
    ap.add_argument("--pdf", help="특정 PDF 파일명 (파일명만, 경로 제외)")
    ap.add_argument("--pollster", help="기관명 (--pdf와 함께 사용)")
    ap.add_argument("--pages", type=int, default=3, help="분석할 최대 페이지 수 (기본: 3)")
    ap.add_argument("--dump-text", action="store_true", help="텍스트/테이블 상세 덤프 출력")
    ap.add_argument("--all", action="store_true", default=False, help="전체 미개발 대상 진단")
    args = ap.parse_args()

    print(_hr("═", 70))
    print("PDF 파서 진단 스크립트")
    print(f"PDF 경로: {_PDF_DIR}")
    print(_hr("═", 70))
    print()

    if args.pdf:
        pollster = args.pollster or "미지정"
        diagnose_one(pollster, args.pdf, max_pages=args.pages, dump_text=args.dump_text)
    else:
        # 기본: 전체 미개발 대상
        for pollster, filename in TARGETS:
            diagnose_one(pollster, filename, max_pages=args.pages, dump_text=args.dump_text)

    print(_hr("═", 70))
    print("진단 완료")


if __name__ == "__main__":
    main()
