import pytest

from lawdigest_ai.processor.category_classifier import (
    classify_by_committee,
    classify_by_content,
    classify_bill,
)


@pytest.mark.parametrize(
    ("committee", "expected"),
    [
        ("법제사법위원회", "justice"),
        ("법사위", "justice"),
        ("기획재정위원회", "economy"),
        ("재정경제기획위원회", "economy"),   # 옛 명칭 별칭
        ("정무위원회", "economy"),
        ("교육위원회", "education"),
        ("과학기술정보방송통신위원회", "tech"),
        ("외교통일위원회", "diplomacy"),
        ("국방위원회", "diplomacy"),
        ("정보위원회", "diplomacy"),          # 맨 끝 규칙(과방위와 구분)
        ("여성가족위원회", "family"),
        ("성평등가족위원회", "family"),        # 개칭 별칭
        ("국회운영위원회", "politics"),
    ],
)
def test_committee_single_map(committee, expected):
    assert classify_by_committee(committee, "") == expected


@pytest.mark.parametrize(
    ("committee", "text", "expected"),
    [
        ("보건복지위원회", "영유아보육법", "family"),
        ("보건복지위원회", "의료법 일부개정", "health"),
        ("보건복지위원회", "노인복지 지원", "welfare"),          # 기본값
        ("환경노동위원회", "채용절차 공정화", "labor"),
        ("기후에너지환경노동위원회", "근로기준법", "labor"),      # 개칭 + 분할
        ("환경노동위원회", "폐기물관리법", "environment"),        # 기본값
        ("국토교통위원회", "민간임대주택", "housing"),
        ("국토교통위원회", "철도산업발전", "transport"),          # 기본값
        ("행정안전위원회", "도로교통법", "transport"),
        ("행정안전위원회", "재난 및 안전관리", "safety"),
        ("행정안전위원회", "지방교부세법", "politics"),           # 기본값
        ("산업통상자원중소벤처기업위원회", "전기사업법", "environment"),
        ("산업통상자원중소벤처기업위원회", "중소기업진흥", "industry"),  # 기본값
    ],
)
def test_committee_split_map(committee, text, expected):
    assert classify_by_committee(committee, text) == expected


@pytest.mark.parametrize("committee", ["본회의", "-", "", "   ", None])
def test_committee_skip_returns_none(committee):
    assert classify_by_committee(committee, "조세특례제한법") is None


def test_content_law_name_priority_over_summary():
    # 법안명의 법률 종류가 요약 키워드보다 우선.
    assert classify_by_content("국회법 일부개정법률안", "예산안 자동부의 폐지") == "politics"
    assert classify_by_content("재난 및 안전관리 기본법", "감염병 사회재난 지원") == "safety"


@pytest.mark.parametrize(
    ("bill_name", "expected"),
    [
        ("조세특례제한법 일부개정법률안", "economy"),
        ("사립학교법 일부개정법률안", "education"),
        ("약사법 일부개정법률안", "health"),
        ("노동조합 및 노동관계조정법", "labor"),
        ("공직선거법 일부개정법률안", "politics"),
        ("동물보호법 일부개정법률안", "environment"),
        ("양봉산업의 육성 및 지원에 관한 법률", "agriculture"),
        ("공인노무사법 일부개정법률안", "labor"),
        ("주세법 일부개정법률안", "economy"),
        ("관광진흥법 일부개정법률안", "culture"),
        ("법원조직법 일부개정법률안", "justice"),
    ],
)
def test_content_keyword_classification(bill_name, expected):
    assert classify_by_content(bill_name, "") == expected


def test_content_unmatched_returns_none():
    assert classify_by_content("알 수 없는 무언가에 관한 법률", "맥락 없는 문장") is None


def test_classify_bill_prefers_committee_then_content_then_unknown():
    # 위원회 있으면 위원회 매핑
    assert classify_bill("법제사법위원회", "상법 일부개정법률안", "") == "justice"
    # 본회의면 내용 분류
    assert classify_bill("본회의", "조세특례제한법 일부개정법률안", "") == "economy"
    # 위원회도 내용도 못 잡으면 unknown
    assert classify_bill("본회의", "맥락 없는 제목", "맥락 없는 요약") == "unknown"
