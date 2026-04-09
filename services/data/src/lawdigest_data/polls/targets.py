"""수집 대상 선거 타겟 정의 및 매칭 유틸리티."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .models import ListRecord

# config/ 디렉터리 기본 경로 (services/data/config/)
_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"


@dataclass(frozen=True)
class RegionSpec:
    """광역시·도 검색 및 지역 매칭 규칙."""

    key: str
    search_cnd: str = "4"
    search_wrd: str = ""
    region: Optional[str] = None


@dataclass(frozen=True)
class ElectionSpec:
    """선거 공통 정의."""

    key: str
    poll_gubuncd: str
    election_type: Optional[str] = None
    election_names: Optional[Tuple[str, ...]] = None


@dataclass(frozen=True)
class PollTarget:
    """실제 수집 대상.

    런타임에서는 region/election 정의를 조합한 완성형 검색/필터 정보를 제공한다.
    """

    slug: str
    region_key: str
    election_key: str
    search_wrd: str = ""
    search_cnd: str = "4"
    region: Optional[str] = None
    election_names: Optional[Tuple[str, ...]] = None
    election_type: Optional[str] = None
    pollsters: Optional[Tuple[str, ...]] = None
    ignored_analysis_filenames: Optional[Tuple[str, ...]] = None
    poll_gubuncd: str = ""


def _load_region_specs(data: dict) -> dict[str, RegionSpec]:
    regions: dict[str, RegionSpec] = {}
    for key, item in data.get("regions", {}).items():
        regions[key] = RegionSpec(
            key=key,
            search_cnd=str(item.get("search_cnd", "4")),
            search_wrd=item.get("search_wrd", ""),
            region=item.get("region"),
        )
    return regions


def _load_election_specs(data: dict) -> dict[str, ElectionSpec]:
    elections: dict[str, ElectionSpec] = {}
    for key, item in data.get("elections", {}).items():
        election_names = item.get("election_names")
        elections[key] = ElectionSpec(
            key=key,
            poll_gubuncd=item.get("poll_gubuncd", ""),
            election_type=item.get("election_type"),
            election_names=tuple(election_names) if election_names else None,
        )
    return elections


def load_targets(targets_path: Optional[Path] = None) -> List[PollTarget]:
    """poll_targets.json에서 수집 대상 목록을 로드한다."""

    path = targets_path or (_DEFAULT_CONFIG_DIR / "poll_targets.json")
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    regions = _load_region_specs(data)
    elections = _load_election_specs(data)

    targets: List[PollTarget] = []
    for item in data.get("targets", []):
        region_key = item.get("region_key", "")
        election_key = item.get("election_key", "")
        region_spec = regions[region_key]
        election_spec = elections[election_key]
        pollsters = item.get("pollsters")
        ignored_analysis_filenames = item.get("ignored_analysis_filenames")
        targets.append(
            PollTarget(
                slug=item.get("slug", ""),
                region_key=region_key,
                election_key=election_key,
                search_wrd=region_spec.search_wrd,
                search_cnd=region_spec.search_cnd,
                region=region_spec.region,
                election_names=election_spec.election_names,
                election_type=election_spec.election_type,
                pollsters=tuple(pollsters) if pollsters else None,
                ignored_analysis_filenames=(
                    tuple(ignored_analysis_filenames)
                    if ignored_analysis_filenames
                    else None
                ),
                poll_gubuncd=election_spec.poll_gubuncd,
            )
        )
    return targets


_REGION_SUFFIX_RE = re.compile(r"[시군구읍면동리]$")


def parse_title_region(title_region: str) -> Tuple[str, str]:
    """ListRecord.title_region 필드에서 지역과 선거명을 분리한다."""

    text = title_region.strip()
    parts = text.split()

    if parts and parts[0] == "전국":
        return ("전국", " ".join(parts[1:]))

    idx = text.find(" 전체")
    if idx != -1:
        region = text[: idx + len(" 전체")].strip()
        election_name = text[idx + len(" 전체") :].strip()
        return (region, election_name)

    if len(parts) >= 2 and _REGION_SUFFIX_RE.search(parts[1]):
        region = f"{parts[0]} {parts[1]}"
        election_name = " ".join(parts[2:])
        return (region, election_name)

    if len(parts) >= 2:
        return (parts[0], " ".join(parts[1:]))
    return ("", text)


def matches_target(record: ListRecord, target: PollTarget) -> bool:
    """ListRecord가 PollTarget의 기준을 충족하면 True를 반환한다."""

    if (
        target.region is None
        and target.election_names is None
        and target.pollsters is None
    ):
        return True

    region, election_name = parse_title_region(record.title_region)

    if target.region is not None and region != target.region:
        return False

    if target.election_names is not None:
        clean = election_name.replace("(", "").replace(")", "")
        actual = {token for token in re.split(r"[,\s]+", clean) if token}
        if not actual.intersection(set(target.election_names)):
            return False

    if target.pollsters is not None:
        if not any(keyword in record.pollster for keyword in target.pollsters):
            return False

    return True


def is_ignored_analysis_filename(filename: str, target: PollTarget) -> bool:
    """타겟의 제외 PDF 목록과 일치하면 True를 반환한다."""

    if not target.ignored_analysis_filenames:
        return False
    return filename in target.ignored_analysis_filenames
