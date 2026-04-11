"""코리아리서치인터내셔널 파서 단위 테스트."""
from __future__ import annotations

from lawdigest_data.polls.parser import _KoreaResearchInternationalParser
from lawdigest_data.polls.validation import validate_parse_results


_SAMPLE_PAGE = """
<표 4-2> 서울시장 가상대결 오세훈VS박주민
문4-2. 만약 (A)오세훈, (B)박주민의 양자대결 구도로 치러진다면 어느 인물에게 투표하시겠습니까? 보기는 무작위 순입니다.
                        ---------------------------- -------- -------- -------- -------- -------- -------- --------
                        BASE:전체                    조사완료  오세훈   박주민    없다    모름/    없다/    가중값
                                                      사례수                              무응답   모름/     적용
                                                       (명)                                        무응답   사례수
                                                                                                            (명)
                        ---------------------------- -------- -------- -------- -------- -------- -------- --------
                        전                        체   (804)      37       34       26        2       29     (804)
                        ◈           성           ◈
                           남                  성      (405)      41       35       22        2       24     (383)
                        ---------------------------- -------- -------- -------- -------- -------- -------- --------
""".strip("\n")

_SPLIT_PAGE_A = """
<표 3> 서울시장 후보 선호도
문3. 6월3일 서울특별시장 선거에서 출마후보로 거론되고 있는 다음 인물 중 선생님께서는 누가 가장 낫다고 생각하십니까?
                    ---------------------------- -------- -------- -------- -------- -------- -------- -------- --------
                    BASE:전체                     조사완료  A        B        C        D        E        F        G
                                                  사례수
                    ---------------------------- -------- -------- -------- -------- -------- -------- -------- --------
                    전                        체    (801)      24       21       13        8        4        3        2
                    ---------------------------- -------- -------- -------- -------- -------- -------- -------- --------
""".strip("\n")

_SPLIT_PAGE_B = """
<표 3> 서울시장 후보 선호도
문3. 6월3일 서울특별시장 선거에서 출마후보로 거론되고 있는 다음 인물 중 선생님께서는 누가 가장 낫다고 생각하십니까?
                    ---------------------------- -------- -------- -------- -------- -------- -------- -------- --------
                    BASE:전체                     H        I        기타     없다     미정      없다/미정/모름  가중값
                                                                                                            적용
                                                                                                            사례수
                                                                                                             (명)
                    ---------------------------- -------- -------- -------- -------- -------- -------- -------- --------
                    전                        체        1        0        1       15        6       20     (801)
                    ---------------------------- -------- -------- -------- -------- -------- -------- -------- --------
""".strip("\n")

_JEJU_TITLE_SPLIT_PAGE = """
제회 지방선거 제주특별자치도 여론조사
차
9
(2
)
7 l
표
회 지선 관심도
<
1> 9
문
오는 월 일에 도지사
교육감 등을 뽑는 지방선거가 있습니다
1.
6
3
,
?
          ---------------------------- -------- -------- -------- -------- -------- -------- -------- -------- -------- --------
          BASE:전체                     조사완료
          ---------------------------- -------- -------- -------- -------- -------- -------- -------- -------- -------- --------
          전                        체   (800)      28       48       16        6        1       76       23        1     (800)
          ---------------------------- -------- -------- -------- -------- -------- -------- -------- -------- -------- --------
""".strip("\n")


class TestKoreaResearchInternationalParser:
    def test_parses_ascii_art_page_into_question_result(self) -> None:
        parser = _KoreaResearchInternationalParser()

        results = parser.parse([(_SAMPLE_PAGE, [], _SAMPLE_PAGE)])

        assert len(results) == 1
        assert results[0].question_title == "서울시장 가상대결 오세훈VS박주민"
        assert results[0].overall_n_completed == 804
        assert results[0].overall_n_weighted == 804
        assert results[0].response_options == [
            "오세훈",
            "박주민",
            "없다",
            "모름/ 무응답",
        ]
        assert results[0].overall_percentages == [37.0, 34.0, 26.0, 2.0]

    def test_parse_result_passes_validation(self) -> None:
        parser = _KoreaResearchInternationalParser()

        results = parser.parse([(_SAMPLE_PAGE, [], _SAMPLE_PAGE)])

        assert validate_parse_results(results) == {}

    def test_merges_split_pages_and_drops_combined_summary_column(self) -> None:
        parser = _KoreaResearchInternationalParser()

        results = parser.parse(
            [
                (_SPLIT_PAGE_A, [], _SPLIT_PAGE_A),
                (_SPLIT_PAGE_B, [], _SPLIT_PAGE_B),
            ]
        )

        assert len(results) == 1
        assert results[0].question_title == "서울시장 후보 선호도"
        assert results[0].overall_n_completed == 801
        assert results[0].overall_n_weighted is None
        assert results[0].response_options == [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "기타",
            "없다",
            "미정",
        ]
        assert results[0].overall_percentages == [
            24.0,
            21.0,
            13.0,
            8.0,
            4.0,
            3.0,
            2.0,
            1.0,
            0.0,
            1.0,
            15.0,
            6.0,
        ]

    def test_extracts_title_when_leading_digit_is_split_from_text(self) -> None:
        parser = _KoreaResearchInternationalParser()

        title = parser._extract_table_title(_JEJU_TITLE_SPLIT_PAGE)

        assert title == "9회 지선 관심도"

    def test_normalizes_option_label_punctuation_from_words_fallback(self) -> None:
        parser = _KoreaResearchInternationalParser()

        normalized = parser._normalize_option_labels([
            "이정선 현 광주 광역시 교육감 ,",
            "결정 못했다 모름/ 무응답",
        ])

        assert normalized == [
            "이정선 현 광주 광역시 교육감",
            "결정 못했다/ 모름/ 무응답",
        ]
