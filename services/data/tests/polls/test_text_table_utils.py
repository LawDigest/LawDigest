"""코리아리서치 ASCII-art 텍스트 표 유틸 테스트."""
from __future__ import annotations

from lawdigest_data.polls.text_table_utils import (
    extract_ascii_table_blocks,
    infer_column_spans,
    merge_multiline_header,
    parse_total_row,
)


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


class TestExtractAsciiTableBlocks:
    def test_extracts_single_ascii_table_block(self) -> None:
        blocks = extract_ascii_table_blocks(_SAMPLE_PAGE)

        assert len(blocks) == 1
        assert "BASE:전체" in blocks[0]
        assert "전                        체" in blocks[0]


class TestInferColumnSpans:
    def test_infers_spans_from_dash_ruler(self) -> None:
        ruler = _SAMPLE_PAGE.splitlines()[2]

        spans = infer_column_spans(ruler)

        assert len(spans) == 8
        assert spans[0][1] > spans[0][0]
        assert spans[-1][1] > spans[-1][0]


class TestMergeMultilineHeader:
    def test_merges_wrapped_header_lines_into_column_labels(self) -> None:
        lines = _SAMPLE_PAGE.splitlines()
        spans = infer_column_spans(lines[2])

        header = merge_multiline_header(lines[3:7], spans)

        assert header == [
            "BASE:전체",
            "조사완료 사례수 (명)",
            "오세훈",
            "박주민",
            "없다",
            "모름/ 무응답",
            "없다/ 모름/ 무응답",
            "가중값 적용 사례수 (명)",
        ]


class TestParseTotalRow:
    def test_parses_n_completed_percentages_and_n_weighted(self) -> None:
        lines = _SAMPLE_PAGE.splitlines()
        spans = infer_column_spans(lines[2])

        parsed = parse_total_row(lines[8], spans)

        assert parsed.label == "전체"
        assert parsed.n_completed == 804
        assert parsed.percentages == [37.0, 34.0, 26.0, 2.0, 29.0]
        assert parsed.n_weighted == 804
