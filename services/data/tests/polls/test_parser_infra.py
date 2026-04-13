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
    _EmbrainPublicParser,
    _FlowerResearchParser,
    _HangilResearchParser,
    _IpsosParser,
    _KoreanResearchParser,
    _KStatResearchParser,
    _NextResearchParser,
    _RealMeterParser,
    _ResearchAndResearchParser,
    _SignalPulseParser,
    _STIParser,
    _TableFormatParser,
    _DailyResearchParser,
    _WinjiKoreaParser,
)

# ── PARSER_KEY 자동 탐색 ─────────────────────────────────────────────────────


class TestBuildParserKeyMap:
    def test_all_parsers_discovered(self):
        key_map = _build_parser_key_map()
        expected_keys = {
            "_TableFormatParser",
            "_DailyResearchParser",
            "_RealMeterParser",
            "_KoreanResearchParser",
            "_SignalPulseParser",
            "_EmbrainPublicParser",
            "_FlowerResearchParser",
            "_WinjiKoreaParser",
            "_ResearchAndResearchParser",
            "_HangilResearchParser",
            "_NextResearchParser",
            "_STIParser",
            "_IpsosParser",
            "_KStatResearchParser",
            "_AceResearchParser",
            "_KopraParser",
            "_MediaTomatoParser",
            "_KSOIParser",
            "_FairPollParser",
        }
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


# ── PollResultParser 레지스트리 로드 ─────────────────────────────────────────


class TestPollResultParserRegistry:
    def test_load_from_default_registry(self):
        """기본 경로의 parser_registry.json에서 모든 파서가 로드된다."""
        parser = PollResultParser()
        assert len(parser._registry) == 19  # 현재 등록된 파서 수

    def test_all_pollsters_registered(self):
        parser = PollResultParser()
        all_keywords = {kw for e in parser._registry for kw in e.pollster_keywords}
        expected = {
            "조원씨앤아이",
            "메타서치",
            "데일리리서치",
            "리얼미터",
            "한국리서치",
            "시그널앤펄스",
            "엠브레인퍼블릭",
            "여론조사꽃",
            "윈지코리아",
            "(주)한길리서치",
            "한길리서치",
            "리서치앤리서치",
            "㈜리서치앤리서치",
            "(주)리서치앤리서치",
            "넥스트리서치",
            "에스티아이",
            "㈜에스티아이",
            "(주)에스티아이",
            "입소스",
            "Ipsos",
            "케이스탯리서치",
            "㈜케이스탯리서치",
            "(주)케이스탯리서치",
            "케이스탯",
            "메타보이스",
            "메타보이스(주)",
            # 신규 추가 파서
            "(주)에이스리서치",
            "에이스리서치",
            "KOPRA",
            "한국여론평판연구소",
            "미디어토마토",
            "케이에스오아이 주식회사(한국사회여론연구소)",
            "KSOI",
            "한국사회여론연구소",
            # 여론조사공정
            "여론조사공정(주)",
            "여론조사공정",
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
