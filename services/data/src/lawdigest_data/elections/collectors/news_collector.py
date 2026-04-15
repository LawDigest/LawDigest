"""선거 뉴스 수집기 — 네이버 뉴스 검색 API.

API 키 발급 후 환경변수 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET을 설정하여 사용한다.
현재는 stub 구현 — API 키 발급 후 실제 수집 로직을 채운다.

참고: https://developers.naver.com/docs/serviceapi/search/news/news.md
"""

import logging
import os
from datetime import datetime
from typing import Any

from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from lawdigest_data.elections.models.news import ElectionNews

logger = logging.getLogger(__name__)

# 선거별 검색 키워드 목록 (sg_id → keywords)
ELECTION_KEYWORDS: dict[str, list[str]] = {
    "20260603": [
        "2026 지방선거",
        "지방선거 후보",
        "시도지사 선거",
        "구시군장 선거",
        "지방의회 선거",
    ],
}

# 정당명 → matched_party 매핑
PARTY_KEYWORDS: dict[str, str] = {
    "더불어민주당": "더불어민주당",
    "민주당": "더불어민주당",
    "국민의힘": "국민의힘",
    "조국혁신당": "조국혁신당",
    "개혁신당": "개혁신당",
    "진보당": "진보당",
}

_NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"


def _get_naver_headers() -> dict[str, str]:
    client_id = os.environ.get("NAVER_CLIENT_ID", "")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise EnvironmentError(
            "NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경변수를 설정해야 합니다."
        )
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }


def _parse_pub_date(date_str: str) -> datetime:
    """네이버 API 날짜 형식 파싱 (RFC 2822: 'Mon, 12 Apr 2026 09:00:00 +0900')."""
    from email.utils import parsedate_to_datetime

    try:
        return parsedate_to_datetime(date_str).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


def _detect_party(title: str, description: str) -> str | None:
    text = (title or "") + " " + (description or "")
    for keyword, party in PARTY_KEYWORDS.items():
        if keyword in text:
            return party
    return None


def _upsert_news(session: Session, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    stmt = mysql_insert(ElectionNews).values(rows)
    stmt = stmt.on_duplicate_key_update(
        title=stmt.inserted.title,
        description=stmt.inserted.description,
        source=stmt.inserted.source,
        thumbnail_url=stmt.inserted.thumbnail_url,
    )
    session.execute(stmt)
    return len(rows)


class NaverNewsCollector:
    """네이버 뉴스 검색 API를 통한 선거 뉴스 수집기.

    TODO (API 키 발급 후):
    1. NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 환경변수 설정
    2. collect_news() 메서드의 stub 로직을 실제 HTTP 요청으로 교체
    """

    def __init__(self) -> None:
        self._api_available = bool(
            os.environ.get("NAVER_CLIENT_ID") and os.environ.get("NAVER_CLIENT_SECRET")
        )

    def collect_news(self, session: Session, election_id: str, display: int = 100) -> int:
        """선거 관련 뉴스를 수집하여 DB에 저장한다.

        Args:
            session: SQLAlchemy 세션
            election_id: 선거 ID (예: '20260603')
            display: 키워드당 수집 건수 (최대 100)

        Returns:
            수집된 뉴스 건수
        """
        if not self._api_available:
            logger.warning(
                "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 미설정 — 뉴스 수집 스킵"
            )
            return 0

        import requests  # noqa: PLC0415

        headers = _get_naver_headers()
        keywords = ELECTION_KEYWORDS.get(election_id, ["지방선거"])
        total = 0
        batch: list[dict[str, Any]] = []

        for keyword in keywords:
            try:
                resp = requests.get(
                    _NAVER_SEARCH_URL,
                    headers=headers,
                    params={"query": keyword, "display": display, "sort": "date"},
                    timeout=10,
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
            except Exception as exc:
                logger.warning("뉴스 수집 실패 (keyword=%s): %s", keyword, exc)
                continue

            for item in items:
                title = item.get("title", "").replace("<b>", "").replace("</b>", "")
                description = (
                    item.get("description", "") or ""
                ).replace("<b>", "").replace("</b>", "")
                link = item.get("link") or item.get("originallink", "")
                if not link:
                    continue

                batch.append({
                    "election_id": election_id,
                    "title": title[:500],
                    "description": description or None,
                    "link": link[:1000],
                    "original_link": (item.get("originallink") or None),
                    "source": None,  # 네이버 기본 API는 출처 미제공
                    "thumbnail_url": None,
                    "pub_date": _parse_pub_date(item.get("pubDate", "")),
                    "search_keyword": keyword,
                    "matched_party": _detect_party(title, description),
                    "matched_region": None,
                })

        if batch:
            count = _upsert_news(session, batch)
            session.flush()
            total += count

        logger.info("선거 뉴스 총 %d건 수집 완료 (electionId=%s)", total, election_id)
        return total
