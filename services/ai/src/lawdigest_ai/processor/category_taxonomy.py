"""법안 분야(category) 분류 체계 — 단일 소스.

시민 친화 생활영역 기준 17개 분야. AI 분류(경로 1 신규 / 경로 3 본회의 구제)와
위원회 백필이 공유하는 코드/라벨/가이드의 유일한 진실원이다.
설계 근거: output/tab-prototypes/FIELD_TAXONOMY.md (v4).
"""
from __future__ import annotations

from typing import Literal, NamedTuple


class Category(NamedTuple):
    code: str
    label: str
    guide: str  # 법안 내용 기준 분류 가이드(프롬프트용)


# 순서 = 프롬프트 노출 순서. code는 저장값(안정), label은 표시·AI 반환값.
CATEGORIES: tuple[Category, ...] = (
    Category("economy", "경제·세금", "세금·물가·재정·금융·공정거래·국무조정"),
    Category("housing", "부동산·주거", "주택·부동산·임대·재개발·도시정비"),
    Category("transport", "교통·물류", "도로·철도·항공·교통안전·물류·항만"),
    Category("labor", "일자리·노동", "고용·임금·노동권·노조·산업안전·퇴직"),
    Category("environment", "환경·기후·에너지", "환경보호·기후위기·에너지전환·자원순환"),
    Category("welfare", "복지·연금", "기초생활·연금·노인·장애인·아동복지"),
    Category("health", "보건·의료", "의료·건강보험·감염병·의약·간호"),
    Category("education", "교육", "학교·대학·입시·교원·평생교육"),
    Category("family", "가족·청소년", "저출생·보육·여성·청소년·양성평등"),
    Category("industry", "산업·중소기업", "제조·통상·창업·벤처·소상공인"),
    Category("tech", "과학·디지털·AI", "과학기술·AI·정보통신·방송·우주·개인정보·데이터"),
    Category("agriculture", "농림·축산·수산", "농업·축산·산림·수산·식품·먹거리"),
    Category("culture", "문화·예술·체육", "문화·예술·콘텐츠·관광·스포츠"),
    Category("safety", "안전·재난·치안", "재난·소방·경찰·치안·식품안전·재해"),
    Category("politics", "정치·행정", "국회·선거·정당·지방자치·정부조직"),
    Category("diplomacy", "외교·국방", "외교·통상·통일·국방·병역·재외국민·안보"),
    Category("justice", "사법·범죄", "재판·검찰·형사·민사·상사·처벌·헌재"),
)

# 백필 잔차(텍스트조차 없어 분류 불가)용 코드. AI는 절대 출력하지 않는다.
UNKNOWN_CODE = "unknown"
UNKNOWN_LABEL = "미분류"

CATEGORY_CODES: tuple[str, ...] = tuple(c.code for c in CATEGORIES)
CATEGORY_LABELS: tuple[str, ...] = tuple(c.label for c in CATEGORIES)
LABEL_TO_CODE: dict[str, str] = {c.label: c.code for c in CATEGORIES}
CODE_TO_LABEL: dict[str, str] = {c.code: c.label for c in CATEGORIES}

# Pydantic 구조적 출력에서 AI가 고를 수 있는 라벨 enum.
CategoryLabel = Literal[CATEGORY_LABELS]  # type: ignore[valid-type]


def category_label_to_code(label: str | None) -> str:
    """AI가 반환한 라벨을 저장용 코드로 변환. 알 수 없으면 UNKNOWN_CODE."""
    if label is None:
        return UNKNOWN_CODE
    return LABEL_TO_CODE.get(label.strip(), UNKNOWN_CODE)


def build_category_prompt_block() -> str:
    """프롬프트에 넣을 17개 분야 지시문 + 가이드 목록."""
    lines = [f"- {c.label}: {c.guide}" for c in CATEGORIES]
    return (
        "category는 아래 17개 분야 중 법안 내용에 가장 부합하는 정확히 1개의 라벨입니다.\n"
        "라벨 문자열을 그대로 사용하고, 목록에 없는 값이나 빈 값을 쓰지 마세요.\n"
        "법안명에 드러난 법률 종류를 요약 속 부수 키워드보다 우선하세요"
        "(예: '국회법'은 '예산' 언급이 있어도 정치·행정, "
        "'재난 및 안전관리 기본법'은 '감염병' 언급이 있어도 안전·재난·치안).\n"
        "애매하면 가장 가까운 1개를 고르고, 분류를 생략하지 마세요.\n"
        + "\n".join(lines)
    )
