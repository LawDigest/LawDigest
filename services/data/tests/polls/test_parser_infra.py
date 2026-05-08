"""파서 인프라 단위 테스트.

PollResultParser의 레지스트리 로드, 파서 선택, 오류 처리를 검증한다.
PDF 파일이 없어도 실행되는 빠른 테스트.

실행:
    pytest tests/polls/test_parser_infra.py -v
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

from lawdigest_data.polls.parser import (
    PollParser,
    PollResultParser,
    UnknownPollsterError,
    _build_parser_key_map,
    _AceResearchParser,
    _EmbrainPublicParser,
    _FlowerResearchParser,
    _HangilResearchParser,
    _IpsosParser,
    _J2InsightParser,
    _KoreanResearchParser,
    _KStatResearchParser,
    _NextResearchParser,
    _RealMeterParser,
    _ResearchAndResearchParser,
    _ResearchViewParser,
    _SignalPulseParser,
    _STIParser,
    _SETInnovationParser,
    _TableFormatParser,
    _DailyResearchParser,
    _WinjiKoreaParser,
)


def _load_registry_config() -> dict:
    registry_path = Path(__file__).resolve().parents[2] / "config" / "parser_registry.json"
    return json.loads(registry_path.read_text(encoding="utf-8"))


# ── PARSER_KEY 자동 탐색 ─────────────────────────────────────────────────────


class TestBuildParserKeyMap:
    def test_all_parsers_discovered(self):
        key_map = _build_parser_key_map()
        registry = _load_registry_config()
        expected_keys = {entry["class"] for entry in registry["parsers"].values()}
        assert expected_keys == set(key_map.keys())

    def test_key_maps_to_correct_class(self):
        key_map = _build_parser_key_map()
        assert key_map["_WinjiKoreaParser"] is _WinjiKoreaParser
        assert key_map["_FlowerResearchParser"] is _FlowerResearchParser
        assert key_map["_DailyResearchParser"] is _DailyResearchParser


# ── PARSER_KEY 클래스 변수 존재 여부 ─────────────────────────────────────────


class TestParserKeyAttribute:
    @pytest.mark.parametrize(
        "parser_cls",
        [
            _TableFormatParser,
            _DailyResearchParser,
            _RealMeterParser,
            _KoreanResearchParser,
            _SignalPulseParser,
            _EmbrainPublicParser,
            _FlowerResearchParser,
            _WinjiKoreaParser,
            _ResearchAndResearchParser,
            _HangilResearchParser,
            _NextResearchParser,
            _STIParser,
            _IpsosParser,
            _KStatResearchParser,
        ],
    )
    def test_has_parser_key(self, parser_cls):
        assert hasattr(parser_cls, "PARSER_KEY"), (
            f"{parser_cls.__name__}에 PARSER_KEY가 없습니다."
        )
        assert isinstance(parser_cls.PARSER_KEY, str)
        assert parser_cls.PARSER_KEY == parser_cls.__name__, (
            f"{parser_cls.__name__}.PARSER_KEY = '{parser_cls.PARSER_KEY}' "
            f"(클래스명과 일치해야 함)"
        )


# ── PollParser Protocol 준수 ─────────────────────────────────────────────────


class TestPollParserProtocol:
    @pytest.mark.parametrize(
        "parser_cls",
        [
            _TableFormatParser,
            _DailyResearchParser,
            _RealMeterParser,
            _KoreanResearchParser,
            _SignalPulseParser,
            _EmbrainPublicParser,
            _FlowerResearchParser,
            _WinjiKoreaParser,
            _ResearchAndResearchParser,
            _HangilResearchParser,
            _NextResearchParser,
            _STIParser,
            _IpsosParser,
            _KStatResearchParser,
        ],
    )
    def test_implements_protocol(self, parser_cls):
        """런타임 Protocol 체크 — parse(pages_data) 시그니처 존재 여부."""
        instance = parser_cls()
        assert isinstance(instance, PollParser), (
            f"{parser_cls.__name__}이 PollParser Protocol을 구현하지 않습니다."
        )

    @pytest.mark.parametrize(
        "parser_cls",
        [
            _TableFormatParser,
            _DailyResearchParser,
            _RealMeterParser,
            _KoreanResearchParser,
            _SignalPulseParser,
            _EmbrainPublicParser,
            _FlowerResearchParser,
            _WinjiKoreaParser,
            _ResearchAndResearchParser,
            _HangilResearchParser,
            _NextResearchParser,
            _STIParser,
            _IpsosParser,
            _KStatResearchParser,
        ],
    )
    def test_parse_accepts_pages_data(self, parser_cls):
        """parse()가 빈 pages_data 리스트를 받아 오류 없이 빈 결과를 반환한다."""
        instance = parser_cls()
        result = instance.parse([])
        assert isinstance(result, list)


class TestDailyResearchParserBehavior:
    def test_uses_parenthesized_question_marker_as_pending_title(self):
        parser = _DailyResearchParser()
        table = [
            ["구 분", "", "조사완료", "가중값", "후보 A", "후보 B"],
            ["전 체", "", "500", "500", "60.0", "40.0"],
        ]

        results = parser.parse(
            [
                (
                    "1) 후보 지지도\n만약 내일 당장 선거가 치러진다면",
                    [],
                    "1) 후보 지지도\n만약 내일 당장 선거가 치러진다면",
                ),
                ("", [table], ""),
            ]
        )

        assert len(results) == 1
        assert results[0].question_title == "후보 지지도"

    def test_prefers_table_title_marker_for_cross_table_pages(self):
        parser = _DailyResearchParser()
        table = [
            ["구 분", "", "조사완료", "가중값", "후보 A", "후보 B"],
            ["전 체", "", "500", "500", "60.0", "40.0"],
        ]

        results = parser.parse(
            [
                ("【표1】 후보 지지도", [table], "【표1】 후보 지지도"),
                ("【표2】 당선가능성", [table], "【표2】 당선가능성"),
            ]
        )

        assert [r.question_title for r in results] == ["후보 지지도", "당선가능성"]

    def test_merges_split_table_pages_with_same_title(self):
        parser = _DailyResearchParser()
        first_table = [
            ["구 분", "", "조사완료", "가중값", "후보 A", "후보 B"],
            ["전 체", "", "500", "500", "45.0", "50.0"],
        ]
        second_table = [
            ["구 분", "", "조사완료", "가중값", "기타", "없음"],
            ["전 체", "", "500", "500", "3.0", "2.0"],
        ]

        results = parser.parse(
            [
                ("【표2-1】 후보 지지도", [first_table], "【표2-1】 후보 지지도"),
                ("【표2-2】 후보 지지도", [second_table], "【표2-2】 후보 지지도"),
            ]
        )

        assert len(results) == 1
        assert results[0].question_title == "후보 지지도"
        assert results[0].response_options == ["후보 A", "후보 B", "기타", "없음"]
        assert results[0].overall_percentages == [45.0, 50.0, 3.0, 2.0]


class TestAceResearchParserBehavior:
    def test_parses_split_table_title_marker(self):
        parser = _AceResearchParser()
        table = [
            ["", None, "사례수", None, "정치적 이념 성향", None],
            [None, None, "조사\n완료", "가중값\n적용", "보수", "진보"],
            ["■ 전 체 ■", None, "(1010)", "(1010)", "60.0", "40.0"],
        ]
        text = "표\n정치적 이념 성향\n<\n1>\nQ4. 정치적 이념 성향은?"

        results = parser.parse([("", [table], text)])

        assert len(results) == 1
        assert results[0].question_number == 1
        assert results[0].question_title == "정치적 이념 성향"
        assert results[0].response_options == ["보수", "진보"]

    def test_drops_summary_tail_when_option_repeats(self):
        parser = _AceResearchParser()
        table = [
            ["", None, "사례수", None, "이재명 대통령 국정 수행 평가", None, None, None, None, None, None, None],
            [
                "",
                None,
                "조사\n완료",
                "가중값\n적용",
                "매우 잘하고 있다",
                "다소 잘하고 있다",
                "다소 잘 못하고 있다",
                "매우 잘 못하고 있다",
                "잘 모르겠다",
                "잘하고 있다",
                "잘 못하고 있다",
                "잘 모르겠다",
            ],
            ["■ 전 체 ■", None, "(1010)", "(1010)", "28.5", "17.4", "16.9", "29.5", "7.7", "45.9", "46.4", "7.7"],
        ]
        text = "표\n이재명 대통령 국정 수행 평가\n<\n2>\nQ5. 국정 수행 평가?"

        results = parser.parse([("", [table], text)])

        assert len(results) == 1
        assert results[0].response_options == [
            "매우 잘하고 있다",
            "다소 잘하고 있다",
            "다소 잘 못하고 있다",
            "매우 잘 못하고 있다",
            "잘 모르겠다",
        ]
        assert results[0].overall_percentages == [28.5, 17.4, 16.9, 29.5, 7.7]


class TestResearchViewParserBehavior:
    def test_uses_latest_compact_date_row_for_trend_table(self):
        parser = _ResearchViewParser()
        table = [
            ["1. 후보지지도\n(%)", None, None, None, None, None],
            ["", None, "조사완료\n(사례수)", "가중값적용\n(사례수)", "후보 A", "후보 B"],
            ["260207-08 (1차)", None, "500", "500", "42.5", "34.6"],
            ["260425-26 (2차)", None, "500", "500", "44.6", "39.8"],
            ["성별", "남성", "238", "254", "46.7", "39.9"],
        ]

        results = parser.parse([("", [table], "")])

        assert len(results) == 1
        assert results[0].question_title == "후보지지도"
        assert results[0].overall_percentages == [44.6, 39.8]


class TestKoreanResearchParserBehavior:
    def test_parses_split_title_with_bunched_total_percentages(self):
        parser = _KoreanResearchParser()
        table = [
            ["전체", "사례수 (명)", None, "후보 A", "후보 B", "없음", "계"],
            [None, "조사완료사례수(명)", "가중값 적용 사례수(명)", None, None, None, None],
            ["▣ 전체 ▣", "(500)", "(500)", "10 20 70 100", None, None, None],
        ]
        text = "표 \n김해시장 지지도\n[\n1]\n문\n선생님께서는 누구를 지지하십니까?"

        results = parser.parse([(text, [table], text)])

        assert len(results) == 1
        assert results[0].question_title == "김해시장 지지도"
        assert results[0].response_options == ["후보 A", "후보 B", "없음"]
        assert results[0].overall_percentages == [10.0, 20.0, 70.0]


class TestRealMeterParserBehavior:
    def test_uses_question_line_before_bare_q_marker(self):
        parser = _RealMeterParser()
        table = [
            ["구 분", None, "조사\n완료\n사례수", "가중값\n적용\n사례수", "정책 A", "정책 B"],
            ["전체", None, "(804) (804)", None, "18.2", "15.4"],
        ]
        text = "다음에서 제시되는 정책 중 가장 중요하다고 생각하시는 항목을 선택해주십시오\nQ1.\n‘\n’\n."

        results = parser.parse([("", [table], text)])

        assert len(results) == 1
        assert results[0].question_number == 1
        assert results[0].question_title == (
            "다음에서 제시되는 정책 중 가장 중요하다고 생각하시는 항목을 선택해주십시오"
        )
        assert results[0].overall_percentages == [18.2, 15.4]

    def test_merges_split_pages_with_same_question_number(self):
        parser = _RealMeterParser()
        first_table = [
            ["구 분", None, "조사\n완료\n사례수", "가중값\n적용\n사례수", "정책 A", "정책 B"],
            ["전체", None, "(804) (804)", None, "40.0", "35.0"],
        ]
        second_table = [
            ["구 분", None, "조사\n완료\n사례수", "가중값\n적용\n사례수", "정책 C", "정책 D"],
            ["전체", None, "(804) (804)", None, "15.0", "10.0"],
        ]
        first_text = "광역단체 정책의제\nQ1."
        second_text = "광역단체 정책의제\nQ1."

        results = parser.parse([("", [first_table], first_text), ("", [second_table], second_text)])

        assert len(results) == 1
        assert results[0].response_options == ["정책 A", "정책 B", "정책 C", "정책 D"]
        assert results[0].overall_percentages == [40.0, 35.0, 15.0, 10.0]

    def test_recovers_fragmented_first_option_and_percentage(self):
        parser = _RealMeterParser()
        table = [
            ["", None, None, None, None, None, None, None, None],
            [
                "구",
                "조사\n분 완료\n사례수",
                "가중값\n적용 박\n사례수",
                "효진",
                "성기선",
                "안민석",
                "유은혜",
                "없음",
                "잘 모름",
            ],
            ["전 체", "(1001)", "(1001) 1", "2.03", "12.60", "20.17", "22.99", "16.36", "15.85"],
        ]

        result = parser._extract_from_tables([table], "단일후보 적합도", "단일후보 적합도")

        assert result is not None
        assert result.response_options[0] == "박효진"
        assert result.overall_percentages[0] == 12.03
        assert round(sum(result.overall_percentages), 2) == 100.0

    def test_uses_pending_title_when_table_page_has_no_q_marker(self):
        parser = _RealMeterParser()
        table = [
            ["", None, None, None, None, None, None, None, None],
            [
                "구",
                "조사\n분 완료\n사례수",
                "가중값\n적용 박\n사례수",
                "효진",
                "성기선",
                "안민석",
                "유은혜",
                "없음",
                "잘 모름",
            ],
            ["전 체", "(1001)", "(1001) 1", "2.03", "12.60", "20.17", "22.99", "16.36", "15.85"],
        ]

        results = parser.parse([("단일후보 적합도", [], "단일후보 적합도"), ("", [table], "")])

        assert len(results) == 1
        assert results[0].question_title == "단일후보 적합도"


# ── PollResultParser 레지스트리 로드 ─────────────────────────────────────────


class TestPollResultParserRegistry:
    def test_load_from_default_registry(self):
        """기본 경로의 parser_registry.json에서 모든 파서가 로드된다."""
        parser = PollResultParser()
        registry = _load_registry_config()
        assert len(parser._registry) == len(registry["parsers"])

    def test_all_pollsters_registered(self):
        parser = PollResultParser()
        all_keywords = {kw for e in parser._registry for kw in e.pollster_keywords}
        registry = _load_registry_config()
        expected = {
            pollster
            for entry in registry["parsers"].values()
            for pollster in entry["pollster_names"]
        }
        assert expected == all_keywords

    def test_registry_json_missing_raises(self, tmp_path):
        """존재하지 않는 경로 → RuntimeError."""
        with pytest.raises(RuntimeError, match="parser_registry.json"):
            PollResultParser(registry_path=tmp_path / "nonexistent.json")

    def test_registry_unknown_class_raises(self, tmp_path):
        """JSON에 미등록 class명 → RuntimeError."""
        bad_registry = {
            "parsers": {
                "unknown_format": {
                    "class": "_NonExistentParser",
                    "pollster_names": ["테스트기관"],
                }
            }
        }
        registry_path = tmp_path / "bad_registry.json"
        registry_path.write_text(json.dumps(bad_registry), encoding="utf-8")
        with pytest.raises(RuntimeError, match="_NonExistentParser"):
            PollResultParser(registry_path=registry_path)


# ── 파서 선택 / UnknownPollsterError ────────────────────────────────────────


class TestSelectParser:
    def setup_method(self):
        self.parser = PollResultParser()

    def test_select_winji_korea(self):
        cls = self.parser._select_parser("(주)윈지코리아컨설팅")
        assert cls is _WinjiKoreaParser

    def test_select_flower_research(self):
        cls = self.parser._select_parser("여론조사꽃")
        assert cls is _FlowerResearchParser

    def test_select_realmeter(self):
        cls = self.parser._select_parser("리얼미터")
        assert cls is _RealMeterParser

    def test_select_meta_voice(self):
        cls = self.parser._select_parser("메타보이스(주)")
        assert cls is _TableFormatParser

    def test_select_research_and_research(self):
        cls = self.parser._select_parser("(주)리서치앤리서치")
        assert cls is _ResearchAndResearchParser

    def test_select_j2_insight(self):
        cls = self.parser._select_parser("제이투인사이트랩")
        assert cls is _J2InsightParser

    def test_select_set_innovation(self):
        cls = self.parser._select_parser("(주)에스티이노베이션")
        assert cls is _SETInnovationParser

    def test_unknown_pollster_raises(self):
        with pytest.raises(UnknownPollsterError, match="미등록기관"):
            self.parser._select_parser("미등록기관")

    def test_none_hint_raises(self):
        with pytest.raises(UnknownPollsterError):
            self.parser._select_parser(None)

    def test_error_message_lists_registered(self):
        """오류 메시지에 등록된 기관 키워드 목록이 포함된다."""
        with pytest.raises(UnknownPollsterError) as exc_info:
            self.parser._select_parser("없는기관")
        assert "윈지코리아" in str(exc_info.value)
        assert "리얼미터" in str(exc_info.value)


class _FakeFinder:
    def __init__(self, tables):
        self.tables = tables


class _FakePage:
    def __init__(self, text, finder):
        self._text = text
        self._finder = finder
        self.find_tables_calls = 0

    def get_text(self, mode=None):
        if mode == "words":
            return []
        return self._text

    def find_tables(self):
        self.find_tables_calls += 1
        return self._finder


class _FakeDoc:
    def __init__(self, pages):
        self._pages = pages

    def __iter__(self):
        return iter(self._pages)

    def close(self):
        return None


class TestParsePdfExtraction:
    def _build_registry(self, tmp_path: Path) -> Path:
        registry = {
            "parsers": {
                "realmeter_format": {
                    "class": "_RealMeterParser",
                    "pollster_names": ["리얼미터"],
                }
            }
        }
        path = tmp_path / "parser_registry.json"
        path.write_text(json.dumps(registry), encoding="utf-8")
        return path

    def test_handles_none_table_finder(self, monkeypatch, tmp_path):
        registry_path = self._build_registry(tmp_path)
        page = _FakePage("1. 서울특별시장 후보 지지도\nQ1. 테스트?", None)
        fake_fitz = types.SimpleNamespace(open=lambda _path: _FakeDoc([page]))
        monkeypatch.setitem(sys.modules, "fitz", fake_fitz)

        parser = PollResultParser(registry_path=registry_path)
        results = parser.parse_pdf(tmp_path / "dummy.pdf", pollster_hint="리얼미터")

        assert results == []
        assert page.find_tables_calls == 1

    def test_realmeter_skips_table_scan_on_non_question_pages(
        self, monkeypatch, tmp_path
    ):
        registry_path = self._build_registry(tmp_path)
        intro_page = _FakePage(
            "서울특별시지방선거및현안조사\n2025. 12.", _FakeFinder([])
        )
        question_page = _FakePage(
            "1. 서울특별시장 후보 지지도\nQ1. 테스트?", _FakeFinder([])
        )
        fake_fitz = types.SimpleNamespace(
            open=lambda _path: _FakeDoc([intro_page, question_page])
        )
        monkeypatch.setitem(sys.modules, "fitz", fake_fitz)

        parser = PollResultParser(registry_path=registry_path)
        parser.parse_pdf(tmp_path / "dummy.pdf", pollster_hint="리얼미터")

        assert intro_page.find_tables_calls == 0
        assert question_page.find_tables_calls == 1


class TestRealMeterParserVariants:
    def test_parses_virtual_match_heading_with_leading_dash(self):
        parser = _RealMeterParser()
        pages_data = [
            (
                "– 3. 가상대결 1 박주민 vs 오세훈\nQ3. 다음은 가상대결 질문입니다.",
                [
                    [
                        [
                            "구 분",
                            None,
                            "조사\n완료\n사례수",
                            "가중값\n적용\n사례수",
                            "더불어민주당\n박주민",
                            "국민의힘\n오세훈",
                            "없음",
                            "잘 모름",
                        ],
                        [
                            "전체",
                            None,
                            "(808) (808)",
                            None,
                            "48.2",
                            "35.2",
                            "10.6",
                            "6.0",
                        ],
                    ]
                ],
                "",
            )
        ]

        results = parser.parse(pages_data)

        assert len(results) == 1
        assert results[0].question_number == 3
        assert results[0].question_title == "가상대결 1 박주민 vs 오세훈"
        assert results[0].response_options == [
            "더불어민주당 박주민",
            "국민의힘 오세훈",
            "없음",
            "잘 모름",
        ]


class TestFlowerResearchParserVariants:
    def test_falls_back_when_total_row_label_is_garbled(self):
        parser = _FlowerResearchParser()
        pages_data = [
            (
                "1. 정당지지도 (1)\nQ 정당지지도 질문",
                [
                    [
                        [
                            "Base=전체",
                            None,
                            "조사완료",
                            "더불어 민주당",
                            "국민의힘",
                            "잘 모름",
                            "가중값 적용 사례수",
                        ],
                        ["먉뺹", None, "(2004)", "56.1", "29.3", "0.4", "(2004)"],
                    ]
                ],
                "",
            )
        ]

        results = parser.parse(pages_data)

        assert len(results) == 1
        assert results[0].question_number == 1
        assert results[0].overall_n_completed == 2004
        assert results[0].overall_n_weighted == 2004
        assert results[0].response_options == ["더불어 민주당", "국민의힘", "잘 모름"]
        assert results[0].overall_percentages == [56.1, 29.3, 0.4]


class TestResearchAndResearchParserVariants:
    def test_parses_research_and_research_table(self):
        parser = _ResearchAndResearchParser()
        pages_data = [
            (
                "",
                [
                    [
                        [
                            "",
                            None,
                            "사례수",
                            None,
                            "매우 잘하고 있다",
                            "대체로 잘하는 편이다",
                            "잘 모르겠다",
                            "계",
                        ],
                        [
                            None,
                            None,
                            "조사 완료 사례수",
                            "가중 적용 사례수",
                            "%",
                            "%",
                            "%",
                            "%",
                        ],
                        [
                            "■ 전 체 ■",
                            None,
                            "(802)",
                            "(802)",
                            "30.7",
                            "27.1",
                            "11.2",
                            "100.0",
                        ],
                    ]
                ],
                "표 이재명 대통령 국정 수행 평가 1 【 】",
            )
        ]

        results = parser.parse(pages_data)

        assert len(results) == 1
        assert results[0].question_title == "이재명 대통령 국정 수행 평가"
        assert results[0].overall_n_completed == 802
        assert results[0].overall_n_weighted == 802
        assert results[0].response_options == [
            "매우 잘하고 있다",
            "대체로 잘하는 편이다",
            "잘 모르겠다",
        ]
        assert results[0].overall_percentages == [30.7, 27.1, 11.2]


class TestEmbrainPublicParserVariants:
    def test_skips_respondent_characteristic_meta_table(self):
        parser = _EmbrainPublicParser()
        pages_data = [
            (
                "[표1] 응답자 특성별 가중값 배율\nQ1. 응답자 특성표",
                [
                    [
                        [
                            "구분",
                            None,
                            None,
                            None,
                            "사례수(B)",
                            "%",
                        ],
                        [
                            "■ 전체 ■",
                            None,
                            "(2009)",
                            "(2009)",
                            "100.0",
                            "1.0",
                        ],
                    ]
                ],
                "[표1] 응답자 특성별 가중값 배율",
            )
        ]

        results = parser.parse(pages_data)

        assert results == []


class TestWinjiKoreaParserRealPdf:
    def test_parses_250915_pdf(self):
        parser = PollResultParser()
        pdf_path = (
            Path(__file__).resolve().parents[2]
            / "output"
            / "pdfs"
            / "제9회 전국동시지방선거"
            / "경기도 전체"
            / "250915_보고서_드림투데이(경기)_v2.pdf"
        )

        results = parser.parse_pdf(pdf_path, pollster_hint="(주)윈지코리아컨설팅")

        assert len(results) == 7
        assert results[0].question_number == 1
        assert results[0].question_title == "이재명 대통령 지지도"
        assert results[0].overall_n_completed == 1002
        assert results[0].overall_n_weighted == 1002
        assert results[0].response_options == [
            "매우 잘하고 있다",
            "대체로 잘하는 편이다",
            "대체로 잘못하는 편이다",
            "매우 잘못하고 있다",
            "잘 모르겠다",
        ]

    def test_parses_260305_pdf(self):
        parser = PollResultParser()
        pdf_path = (
            Path(__file__).resolve().parents[2]
            / "output"
            / "pdfs"
            / "제9회 전국동시지방선거"
            / "경기도 전체"
            / "260305_공표용보고서_경기도_정치지형조사_v2.pdf"
        )

        results = parser.parse_pdf(pdf_path, pollster_hint="(주)윈지코리아컨설팅")

        assert len(results) == 10
        assert results[0].question_number == 1
        assert results[0].overall_n_completed == 1007
        assert results[0].overall_n_weighted is None
        assert all(result.response_options for result in results)
