"""파서 인프라 단위 테스트.

PollResultParser의 레지스트리 로드, 파서 선택, 오류 처리를 검증한다.
PDF 파일이 없어도 실행되는 빠른 테스트.

실행:
    pytest tests/polls/test_parser_infra.py -v
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from lawdigest_data.polls.parser import (
    PollParser,
    PollResultParser,
    UnknownPollsterError,
    _build_parser_key_map,
    _EmbrainPublicParser,
    _FlowerResearchParser,
    _KoreanResearchParser,
    _RealMeterParser,
    _SignalPulseParser,
    _TableFormatParser,
    _TextFormatParser,
    _WinjiKoreaParser,
)


# ── PARSER_KEY 자동 탐색 ─────────────────────────────────────────────────────

class TestBuildParserKeyMap:
    def test_all_parsers_discovered(self):
        key_map = _build_parser_key_map()
        expected_keys = {
            "_TableFormatParser",
            "_TextFormatParser",
            "_RealMeterParser",
            "_KoreanResearchParser",
            "_SignalPulseParser",
            "_EmbrainPublicParser",
            "_FlowerResearchParser",
            "_WinjiKoreaParser",
        }
        assert expected_keys == set(key_map.keys())

    def test_key_maps_to_correct_class(self):
        key_map = _build_parser_key_map()
        assert key_map["_WinjiKoreaParser"] is _WinjiKoreaParser
        assert key_map["_FlowerResearchParser"] is _FlowerResearchParser
        assert key_map["_TextFormatParser"] is _TextFormatParser


# ── PARSER_KEY 클래스 변수 존재 여부 ─────────────────────────────────────────

class TestParserKeyAttribute:
    @pytest.mark.parametrize("parser_cls", [
        _TableFormatParser,
        _TextFormatParser,
        _RealMeterParser,
        _KoreanResearchParser,
        _SignalPulseParser,
        _EmbrainPublicParser,
        _FlowerResearchParser,
        _WinjiKoreaParser,
    ])
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
    @pytest.mark.parametrize("parser_cls", [
        _TableFormatParser,
        _TextFormatParser,
        _RealMeterParser,
        _KoreanResearchParser,
        _SignalPulseParser,
        _EmbrainPublicParser,
        _FlowerResearchParser,
        _WinjiKoreaParser,
    ])
    def test_implements_protocol(self, parser_cls):
        """런타임 Protocol 체크 — parse(pages_data) 시그니처 존재 여부."""
        instance = parser_cls()
        assert isinstance(instance, PollParser), (
            f"{parser_cls.__name__}이 PollParser Protocol을 구현하지 않습니다."
        )

    @pytest.mark.parametrize("parser_cls", [
        _TableFormatParser,
        _TextFormatParser,
        _RealMeterParser,
        _KoreanResearchParser,
        _SignalPulseParser,
        _EmbrainPublicParser,
        _FlowerResearchParser,
        _WinjiKoreaParser,
    ])
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
        assert len(parser._registry) == 8  # 현재 등록된 파서 수

    def test_all_pollsters_registered(self):
        parser = PollResultParser()
        all_keywords = {kw for e in parser._registry for kw in e.pollster_keywords}
        expected = {"조원씨앤아이", "메타서치", "데일리리서치", "리얼미터",
                    "한국리서치", "시그널앤펄스", "엠브레인퍼블릭", "여론조사꽃", "윈지코리아"}
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
                    "pollster_names": ["테스트기관"]
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
