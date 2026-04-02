"""수집 대상 선거 타겟 정의 및 매칭 유틸리티."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .models import ListRecord

# config/ 디렉터리 기본 경로 (services/data/config/)
_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[4] / "config"


@dataclass(frozen=True)
class PollTarget:
    """수집 대상 선거를 정의하는 불변 데이터클래스.

    search_keyword로 NESDC searchWrd 검색을 수행한 뒤,
    region / election_names / pollsters 조건으로 클라이언트 사이드 필터링한다.
    """
    search_keyword: str
    region: Optional[str] = None
    election_names: Optional[Tuple[str, ...]] = None
    election_type: Optional[str] = None
    pollsters: Optional[Tuple[str, ...]] = None  # 조사기관명 OR 필터 (None = 전체)
    slug: str = ""
    poll_gubuncd: str = ""  # NESDC pollGubuncd 파라미터 (예: VT026)


def load_targets(targets_path: Optional[Path] = None) -> List[PollTarget]:
    """poll_targets.json에서 수집 대상 목록을 로드한다.

    targets_path가 None이면 config/poll_targets.json을 자동으로 찾는다.
    파일이 없으면 빈 리스트를 반환한다.
    """
    path = targets_path or (_DEFAULT_CONFIG_DIR / "poll_targets.json")
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    targets: List[PollTarget] = []
    for item in data.get("targets", []):
        election_names = item.get("election_names")
        pollsters = item.get("pollsters")
        targets.append(PollTarget(
            search_keyword=item["search_keyword"],
            region=item.get("region"),
            election_names=tuple(election_names) if election_names else None,
            election_type=item.get("election_type"),
            pollsters=tuple(pollsters) if pollsters else None,
            slug=item.get("slug", ""),
            poll_gubuncd=item.get("poll_gubuncd", ""),
        ))
    return targets


_REGION_SUFFIX_RE = re.compile(r"[시군구읍면동리]$")


def parse_title_region(title_region: str) -> Tuple[str, str]:
    """ListRecord.title_region 필드에서 지역과 선거명을 분리한다.

    지역 끝 판별 규칙 (우선순위순):
      1. "전국" 으로 시작하면 → region = "전국"
      2. " 전체" 가 포함되면 → region = "... 전체" 까지
      3. 두 번째 토큰이 시/군/구/읍/면/동/리 로 끝나면 → region = 첫 두 토큰
      4. 그 외 → region = 첫 토큰
    """
    text = title_region.strip()
    parts = text.split()

    if parts and parts[0] == "전국":
        return ("전국", " ".join(parts[1:]))

    idx = text.find(" 전체")
    if idx != -1:
        region = text[: idx + len(" 전체")].strip()
        election_name = text[idx + len(" 전체"):].strip()
        return (region, election_name)

    if len(parts) >= 2 and _REGION_SUFFIX_RE.search(parts[1]):
        region = f"{parts[0]} {parts[1]}"
        election_name = " ".join(parts[2:])
        return (region, election_name)

    if len(parts) >= 2:
        return (parts[0], " ".join(parts[1:]))
    return ("", text)


def matches_target(record: ListRecord, target: PollTarget) -> bool:
    """ListRecord가 PollTarget의 기준을 충족하면 True를 반환한다.

    - region: None이면 와일드카드, 값이 있으면 파싱된 지역과 정확히 일치
    - election_names: None이면 와일드카드, 값이 있으면 OR 매칭
    - pollsters: None이면 와일드카드, 값이 있으면 record.pollster에 키워드 포함 여부 OR
    """
    if target.region is None and target.election_names is None and target.pollsters is None:
        return True

    region, election_name = parse_title_region(record.title_region)

    if target.region is not None and region != target.region:
        return False

    if target.election_names is not None:
        clean = election_name.replace("(", "").replace(")", "")
        actual = {t for t in re.split(r"[,\s]+", clean) if t}
        if not actual.intersection(set(target.election_names)):
            return False

    if target.pollsters is not None:
        if not any(kw in record.pollster for kw in target.pollsters):
            return False

    return True
