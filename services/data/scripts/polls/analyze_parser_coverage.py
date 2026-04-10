"""제9회 지방선거 여론조사 파서 커버리지 분석.

수집된 전국 목록(all_regions_9th.json)과 parser_registry.json을 대조하여
파서 대응/미대응 현황을 도출한다.

사용법:
    cd services/data
    python scripts/polls/analyze_parser_coverage.py

출력:
    output/polls/coverage/coverage_report.json  — 분석 결과 JSON
    stdout                                      — 요약 리포트
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BASE / "src"))


# ── 로딩 ─────────────────────────────────────────────────────────────────────────

def load_records(json_path: Path) -> List[Dict]:
    return json.loads(json_path.read_text(encoding="utf-8"))


def load_registry(registry_path: Path) -> Dict:
    return json.loads(registry_path.read_text(encoding="utf-8"))


# ── 파서 매핑 구축 ────────────────────────────────────────────────────────────────

def build_parser_lookup(registry: Dict) -> Tuple[Dict[str, str], Set[str]]:
    """(정규화된_기관명 → parser_key) 매핑과 파싱불가 기관 집합을 반환한다."""
    lookup: Dict[str, str] = {}
    for parser_key, info in registry.get("parsers", {}).items():
        for name in info.get("pollster_names", []):
            lookup[_norm(name)] = parser_key

    unparseable: Set[str] = set()
    for item in registry.get("unparseable", {}).get("pollsters", []):
        unparseable.add(_norm(item["name"]))

    return lookup, unparseable


def _norm(name: str) -> str:
    """기관명 정규화: 주식회사 표기, 특수문자, 공백을 통일한다."""
    import re
    name = name.strip()
    # (주) 또는 주식회사 제거
    name = re.sub(r"^\(주\)\s*", "", name)
    name = re.sub(r"\s*\(주\)$", "", name)
    name = re.sub(r"^주식회사\s*", "", name)
    # 공백 정규화
    name = re.sub(r"\s+", " ", name).strip()
    return name


# ── 커버리지 분류 ─────────────────────────────────────────────────────────────────

STATUS_SUPPORTED = "supported"           # 파서 있음
STATUS_UNPARSEABLE = "unparseable"       # 구조적 파싱불가 (공식 판정)
STATUS_UNCOVERED = "uncovered"           # 미개발


def classify_pollster(
    raw_name: str,
    parser_lookup: Dict[str, str],
    unparseable: Set[str],
) -> Tuple[str, Optional[str]]:
    """(status, parser_key) 반환. parser_key는 미개발이면 None."""
    norm = _norm(raw_name)

    # 1) 직접 매칭
    if norm in parser_lookup:
        return STATUS_SUPPORTED, parser_lookup[norm]

    # 2) 파싱불가 목록
    if norm in unparseable:
        return STATUS_UNPARSEABLE, None

    # 3) 부분 매칭 (registry 이름이 raw_name에 포함되거나 그 반대)
    for registry_norm, pkey in parser_lookup.items():
        if registry_norm in norm or norm in registry_norm:
            return STATUS_SUPPORTED, pkey

    # 4) 파싱불가 부분 매칭
    for up_norm in unparseable:
        if up_norm in norm or norm in up_norm:
            return STATUS_UNPARSEABLE, None

    return STATUS_UNCOVERED, None


# ── 분석 ─────────────────────────────────────────────────────────────────────────

def analyze(records: List[Dict], registry: Dict) -> Dict:
    parser_lookup, unparseable = build_parser_lookup(registry)

    # 기관별 집계
    pollster_counter: Counter = Counter(r["pollster"] for r in records)
    province_pollster: Dict[str, Set[str]] = defaultdict(set)
    for r in records:
        province_pollster[r["province"]].add(r["pollster"])

    # 분류
    supported_pollsters: Dict[str, Dict] = {}    # raw_name → {count, parser_key, provinces}
    uncovered_pollsters: Dict[str, Dict] = {}
    unparseable_pollsters: Dict[str, Dict] = {}

    pollster_province_map: Dict[str, Set[str]] = defaultdict(set)
    for r in records:
        pollster_province_map[r["pollster"]].add(r["province"])

    for raw_name, count in pollster_counter.items():
        status, pkey = classify_pollster(raw_name, parser_lookup, unparseable)
        provinces = sorted(pollster_province_map[raw_name])
        entry = {
            "pollster": raw_name,
            "count": count,
            "provinces": provinces,
        }
        if status == STATUS_SUPPORTED:
            entry["parser_key"] = pkey
            supported_pollsters[raw_name] = entry
        elif status == STATUS_UNPARSEABLE:
            unparseable_pollsters[raw_name] = entry
        else:
            uncovered_pollsters[raw_name] = entry

    # 집계
    total_records = len(records)
    total_unique_pollsters = len(pollster_counter)

    supported_records = sum(e["count"] for e in supported_pollsters.values())
    unparseable_records = sum(e["count"] for e in unparseable_pollsters.values())
    uncovered_records = sum(e["count"] for e in uncovered_pollsters.values())

    supported_pct = supported_records / total_records * 100 if total_records else 0
    unparseable_pct = unparseable_records / total_records * 100 if total_records else 0
    uncovered_pct = uncovered_records / total_records * 100 if total_records else 0

    # 지역별 커버리지
    province_coverage: Dict[str, Dict] = {}
    province_totals: Counter = Counter(r["province"] for r in records)
    province_supported: Counter = Counter()
    province_uncovered: Counter = Counter()
    province_unparseable: Counter = Counter()
    for r in records:
        status, _ = classify_pollster(r["pollster"], parser_lookup, unparseable)
        if status == STATUS_SUPPORTED:
            province_supported[r["province"]] += 1
        elif status == STATUS_UNPARSEABLE:
            province_unparseable[r["province"]] += 1
        else:
            province_uncovered[r["province"]] += 1

    for province, total in sorted(province_totals.items(), key=lambda x: -x[1]):
        s = province_supported[province]
        u = province_uncovered[province]
        p = province_unparseable[province]
        province_coverage[province] = {
            "total": total,
            "supported": s,
            "uncovered": u,
            "unparseable": p,
            "coverage_pct": round(s / total * 100, 1) if total else 0,
        }

    return {
        "summary": {
            "total_records": total_records,
            "total_unique_pollsters": total_unique_pollsters,
            "supported_records": supported_records,
            "unparseable_records": unparseable_records,
            "uncovered_records": uncovered_records,
            "supported_pct": round(supported_pct, 1),
            "unparseable_pct": round(unparseable_pct, 1),
            "uncovered_pct": round(uncovered_pct, 1),
            "supported_pollsters_count": len(supported_pollsters),
            "unparseable_pollsters_count": len(unparseable_pollsters),
            "uncovered_pollsters_count": len(uncovered_pollsters),
        },
        "supported_pollsters": sorted(supported_pollsters.values(), key=lambda x: -x["count"]),
        "unparseable_pollsters": sorted(unparseable_pollsters.values(), key=lambda x: -x["count"]),
        "uncovered_pollsters": sorted(uncovered_pollsters.values(), key=lambda x: -x["count"]),
        "province_coverage": province_coverage,
    }


# ── 출력 ─────────────────────────────────────────────────────────────────────────

def print_report(result: Dict) -> None:
    s = result["summary"]
    sep = "─" * 70

    print(sep)
    print("제9회 전국동시지방선거 여론조사 파서 커버리지 분석")
    print(sep)
    print(f"  총 여론조사 건수:         {s['total_records']:>6,}건")
    print(f"  총 조사기관 수:           {s['total_unique_pollsters']:>6}개")
    print()
    print(f"  ✅ 파서 대응 (건수):      {s['supported_records']:>6,}건  ({s['supported_pct']:5.1f}%)  [{s['supported_pollsters_count']}개 기관]")
    print(f"  ❌ 파서 미개발 (건수):    {s['uncovered_records']:>6,}건  ({s['uncovered_pct']:5.1f}%)  [{s['uncovered_pollsters_count']}개 기관]")
    print(f"  ⛔ 파싱불가 (건수):       {s['unparseable_records']:>6,}건  ({s['unparseable_pct']:5.1f}%)  [{s['unparseable_pollsters_count']}개 기관]")
    print(sep)

    print("\n[ 지역별 커버리지 ]")
    print(f"  {'지역':<20} {'전체':>5}  {'대응':>5}  {'미개발':>6}  {'불가':>5}  {'커버율':>7}")
    print("  " + "─" * 58)
    for province, cov in result["province_coverage"].items():
        print(
            f"  {province:<20} {cov['total']:>5}  "
            f"{cov['supported']:>5}  {cov['uncovered']:>6}  "
            f"{cov['unparseable']:>5}  {cov['coverage_pct']:>6.1f}%"
        )

    print(sep)
    print("\n[ 파서 미개발 기관 (건수 내림차순) ]")
    print(f"  {'조사기관':<40} {'건수':>5}  지역")
    print("  " + "─" * 65)
    for item in result["uncovered_pollsters"]:
        provinces_str = ", ".join(item["provinces"][:4])
        if len(item["provinces"]) > 4:
            provinces_str += f" 외 {len(item['provinces'])-4}개"
        print(f"  {item['pollster']:<40} {item['count']:>5}  {provinces_str}")

    print(sep)
    print("\n[ 파싱불가 기관 (구조적 한계) ]")
    for item in result["unparseable_pollsters"]:
        provinces_str = ", ".join(item["provinces"])
        print(f"  {item['pollster']:<40} {item['count']:>5}건  ({provinces_str})")

    print(sep)
    print("\n[ 파서 대응 기관 (건수 내림차순) ]")
    for item in result["supported_pollsters"]:
        print(f"  {item['pollster']:<40} {item['count']:>5}건  [{item['parser_key']}]")
    print(sep)


# ── 메인 ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    records_path = _BASE / "output" / "polls" / "lists" / "all_regions_9th.json"
    registry_path = _BASE / "config" / "parser_registry.json"
    output_dir = _BASE / "output" / "polls" / "coverage"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "coverage_report.json"

    if not records_path.exists():
        print(f"오류: {records_path} 가 없습니다. 먼저 collect_all_regions_poll_list.py를 실행하세요.")
        sys.exit(1)

    records = load_records(records_path)
    registry = load_registry(registry_path)

    result = analyze(records, registry)

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n분석 결과 저장: {output_path}\n")

    print_report(result)


if __name__ == "__main__":
    main()
