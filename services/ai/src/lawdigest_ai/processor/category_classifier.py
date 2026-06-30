"""위원회·내용 기반 분야 분류기 (백필용, 무API).

- classify_by_committee: Bill.committee → 분야 코드 (정식명/약칭/개칭 + 분할 키워드).
- classify_by_content: 법안명+요약 키워드 → 분야 코드 (법안명 우선).
- classify_bill: 위원회 있으면 위원회 매핑, 없거나 미상이면 내용 분류, 그래도 없으면 unknown.

설계·검증: output/tab-prototypes/FIELD_TAXONOMY.md (§4 위원회 매핑, §5.3 본회의 내용 분류).
"""
from __future__ import annotations

import re

from lawdigest_ai.processor.category_taxonomy import UNKNOWN_CODE

# committee 값이면서 분류 불가(위원회 소실/미지정) → 내용 분류로 회부.
_COMMITTEE_SKIP = {"", "본회의", "-"}


def _normalize_committee(committee: str | None) -> str:
    if committee is None:
        return ""
    text = re.sub(r"\([^)]*\)", "", committee.strip())
    text = text.replace("소관위원회", "").replace("소관", "")
    return re.sub(r"\s+", "", text)


# 단일 매핑: (식별 부분문자열들, 코드). 위→아래 첫 매치. 정보는 맨 끝(과방위 오분류 방지).
_COMMITTEE_SINGLE: tuple[tuple[tuple[str, ...], str], ...] = (
    (("과학기술정보방송통신", "과방"), "tech"),
    (("농림축산식품해양수산", "농해수"), "agriculture"),
    (("법제사법", "법사"), "justice"),
    (("문화체육관광", "문체"), "culture"),
    (("재정경제기획",), "economy"),
    (("기획재정", "기재"), "economy"),
    (("외교통일", "외통"), "diplomacy"),
    (("국방",), "diplomacy"),
    (("성평등가족",), "family"),
    (("여성가족", "여가"), "family"),
    (("국회운영", "운영"), "politics"),
    (("기후위기",), "environment"),
    (("정무",), "economy"),
    (("교육",), "education"),
    (("정보",), "diplomacy"),
)

# 분할 매핑: (식별 부분문자열들, [(코드, 키워드정규식)...] 순서대로, 기본코드).
# 키워드는 bill_name+summary 텍스트 대상.
_COMMITTEE_SPLIT: tuple[tuple[tuple[str, ...], tuple[tuple[str, str], ...], str], ...] = (
    (("산업통상자원중소벤처기업", "산자", "산중"),
     (("environment", r"에너지|전력|원자력|신재생|태양광|풍력|수소|발전소|발전사업|방사성|방폐|석탄|연탄|전기차|친환경차|충전|전기사업|전기요금|전기설비"),),
     "industry"),
    (("보건복지",),
     (("family", r"보육|영유아|어린이집"),
      ("health", r"의료|병원|건강|보험|감염|질병|의약|약사|간호|치료|혈액|장기|요양|정신건강|응급|백신")),
     "welfare"),
    (("기후에너지환경노동", "환경노동", "환노"),
     (("labor", r"노동|근로|고용|임금|노조|산재|산업안전|안전보건|채용|일자리|퇴직|실업|최저임금|근로감독|모성보호|육아휴직|정리해고|파업|노사|직장"),),
     "environment"),
    (("국토교통", "국토"),
     (("housing", r"주택|부동산|임대|주거|재개발|재건축|도시정비|분양|전세|월세|건축|택지|리모델링|공동주택"),),
     "transport"),
    (("행정안전", "행안"),
     (("transport", r"도로교통|운전|교통안전"),
      ("safety", r"재난|소방|경찰|치안|화재|재해|위험물|경비|안전관리|방재청")),
     "politics"),
)


def classify_by_committee(committee: str | None, text: str = "") -> str | None:
    """위원회명 → 분야 코드. 매핑 불가(소실/미상/특위)면 None."""
    norm = _normalize_committee(committee)
    if norm in _COMMITTEE_SKIP:
        return None
    for keys, code in _COMMITTEE_SINGLE:
        if any(k in norm for k in keys):
            return code
    for keys, subrules, default in _COMMITTEE_SPLIT:
        if any(k in norm for k in keys):
            for sub_code, pattern in subrules:
                if re.search(pattern, text):
                    return sub_code
            return default
    return None


# 내용 분류: (코드, 키워드정규식) 우선순위 — 특이/구체 도메인 먼저, 일반(politics) 맨 끝.
# 법률명 토큰 중심. 사전 보강(노무사·주세·양봉·동물·수의사·취업·댐 등 §5.3 미매치 반영).
_CONTENT_RULES: tuple[tuple[str, str], ...] = (
    ("justice", r"형법|형사|민법|민사|상법|소송|법원|법관|검찰|검사|변호사|범죄|처벌|형의\s*집행|교정|보호관찰|헌법재판|사면|국가배상|공탁|등기|성폭력|성범죄|아동학대범죄|스토킹|가정폭력|소년법|배상명령|법률구조|공증|중재|인신보호"),
    ("tech", r"정보통신|전기통신|방송|전파|인터넷|소프트웨어|인공지능|지능정보|데이터|개인정보|클라우드|과학기술|연구개발|우주|위성|정보보호|디지털|반도체|콘텐츠산업|전자정부|이러닝|망법|사이버"),
    ("education", r"교육|학교|초등|중등|고등학교|대학|학생|교원|교사|입시|학원|유아교육|평생교육|학위|사립학교|장학|학자금|학교폭력|학술|등록금|교육과정|유치원"),
    ("health", r"의료|병원|의원|건강|보험급여|건강보험|감염병|질병|의약|약사|간호|보건|치료|정신건강|응급|국민건강|의료기기|혈액|장기이식|마약류|식품위생|위생|모자보건|치과|한의|혈액원|장기등|담배|금연|희귀질환|방역|검역"),
    ("family", r"보육|영유아|어린이집|청소년|여성|양성평등|저출산|저출생|한부모|다문화가족|성평등|육아|아이돌봄|건강가정|가족관계|입양|모성|청년기본"),
    ("welfare", r"기초생활|기초연금|국민연금|노인|장애인|아동복지|사회보장|사회복지|복지|기초생활보장|긴급복지|국가유공자|보훈|자립지원|노숙인|장사\s*등|장례|연금|수당|취약계층|고독사|돌봄|보조기기"),
    ("labor", r"노동|근로|노무사|고용|임금|노조|산재|산업안전|안전보건|채용|취업|구직|일자리|퇴직|실업|최저임금|근로감독|모성보호|육아휴직|정리해고|파업|노사|직장|직업안정|직업능력|파견근로|기간제|임금채권"),
    ("housing", r"주택|부동산|임대|주거|재개발|재건축|도시정비|분양|전세|월세|건축|택지|리모델링|공동주택|도시개발|도시계획|국토계획|부동산등기는 제외|주택도시기금|공공주택|소규모주택"),
    ("transport", r"도로|철도|항공|해운|물류|교통|운송|자동차|버스|택시|화물|항만|공항|운수|선박|운전|주차|교통안전|광역교통|대중교통|모빌리티|드론|궤도|여객"),
    ("environment", r"환경|기후|온실가스|탄소|에너지|전력|원자력|신재생|태양광|풍력|수소|발전소|폐기물|재활용|대기|수질|토양|자연|생태|물관리|악취|화학물질|미세먼지|석탄|전기사업|자원순환|상수도|하수도|먹는물|동물|반려동물|동물원|수족관|야생생물|국립공원|댐|하천|수자원|지하수"),
    ("agriculture", r"농업|농어업|농림|축산|산림|수산|어업|농산물|농촌|어촌|임업|종자|가축|농지|농협|수협|해양수산|양곡|식품산업|농수산물|양봉|수의사|동물보건|친환경농|간척|영농|밭농업|말산업|곤충|임산물|해양|어촌"),
    ("culture", r"문화|예술|체육|스포츠|관광|콘텐츠|영화|음악|게임|문화재|저작권|출판|공연|미술|박물관|도서관|문화유산|국악|만화|웹툰|e스포츠|관광진흥|국민체육"),
    ("industry", r"중소기업|소상공인|벤처|창업|특허|상표|디자인보호|무역|통상|수출|제조|상생협력|가맹사업|대규모유통|하도급|유통산업|산업단지|산업기술|중견기업|협동조합|적합성평가|무역기술|국가기술|기업활력|규제자유특구|판로|동반성장"),
    ("economy", r"조세|세금|국세|관세|소득세|법인세|부가가치세|종합부동산세|상속세|증여세|지방세|주세|개별소비세|국가재정|국가회계|예산|기금|금융|은행|보험업|자본시장|증권|공정거래|독점규제|화폐|외환|회계|조달|국유재산|부담금|조세특례|신용|카드|대부업|세무사|서민금융|연체|채권추심|보증"),
    ("diplomacy", r"외교|조약|통일|북한|남북|국방|병역|군인|예비군|재외국민|영사|안보|군사|방위사업|국군|군무원|향토예비군|위안부|독립유공|참전|주한미군|해외파병|재외동포"),
    ("safety", r"재난|소방|경찰|치안|화재|재해|위험물|경비업|안전관리|범죄예방|시설안전|식품안전|총포|화약|풍수해|재해대책|국민안전|생활안전|승강기|수난구조|의용소방"),
    ("politics", r"국회|선거|정당|정치자금|지방자치|지방교부세|공무원|정부조직|행정|국정감사|인사청문|주민|지방재정|국적|주민등록|행정기본|청원|공공기관|부패방지|선거관리|국무|감사원|민원|국경일|상훈|지방의회"),
)
_CONTENT_COMPILED: tuple[tuple[str, "re.Pattern[str]"], ...] = tuple(
    (code, re.compile(pattern)) for code, pattern in _CONTENT_RULES
)


def _match_content(text: str) -> str | None:
    for code, rx in _CONTENT_COMPILED:
        if rx.search(text):
            return code
    return None


def classify_by_content(bill_name: str | None, summary: str | None = None) -> str | None:
    """법안명+요약 키워드 분류. 법안명(법률 종류)을 요약보다 우선. 미매치면 None."""
    name_match = _match_content(bill_name or "")
    if name_match:
        return name_match
    return _match_content(summary or "")


def classify_bill(
    committee: str | None,
    bill_name: str | None,
    summary: str | None = None,
) -> str:
    """백필 오케스트레이터: 위원회 매핑 → 내용 분류 → unknown."""
    text = f"{bill_name or ''} {summary or ''}"
    by_committee = classify_by_committee(committee, text)
    if by_committee is not None:
        return by_committee
    by_content = classify_by_content(bill_name, summary)
    if by_content is not None:
        return by_content
    return UNKNOWN_CODE
