"""스크리닝 결과 데이터 모델 (JSON 직렬화 가능한 dataclass)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MarkerOccurrence:
    """탐지된 마커 패턴 단일 항목."""
    pattern: str
    regex: str
    occurrences: int
    example_pages: List[int] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class QuestionBlockPatterns:
    """질문 블록 구분 패턴 분석 결과."""
    detected_markers: List[MarkerOccurrence] = field(default_factory=list)
    question_numbering_style: str = "unknown"
    estimated_question_count: int = 0


@dataclass
class TotalRowMarkers:
    """전체/합계 행 마커 분석 결과."""
    detected_markers: List[MarkerOccurrence] = field(default_factory=list)
    n_format: str = "unknown"       # e.g. "parenthesized_comma", "plain", "unknown"
    n_examples: List[str] = field(default_factory=list)


@dataclass
class HeaderRowAnalysis:
    """테이블 헤더 행 분석."""
    meta_cols_count: int = 0
    meta_col_labels: List[Optional[str]] = field(default_factory=list)
    option_cols_start_index: int = 0
    option_examples: List[str] = field(default_factory=list)
    has_summary_cols: bool = False
    summary_col_patterns: List[str] = field(default_factory=list)


@dataclass
class RatioFormat:
    """비율 데이터 포맷."""
    decimal_places: int = 1
    is_percentage: bool = True
    examples: List[str] = field(default_factory=list)


@dataclass
class TableStructure:
    """테이블 구조 분석 결과."""
    pages_with_tables: int = 0
    pages_without_tables: int = 0
    typical_shape: Dict[str, int] = field(default_factory=lambda: {"rows": 0, "cols": 0})
    header_row_analysis: HeaderRowAnalysis = field(default_factory=HeaderRowAnalysis)
    ratio_data_location: str = "unknown"    # "table_cell" | "text_bundled" | "mixed"
    ratio_format: RatioFormat = field(default_factory=RatioFormat)
    ratio_cell_bundled: bool = False
    bundled_example: Optional[str] = None


@dataclass
class PageContinuity:
    """페이지 간 질문 연속성 분석."""
    multi_page_questions_detected: bool = False
    continuity_signals: List[str] = field(default_factory=list)
    affected_question_count: int = 0


@dataclass
class ParserTestResult:
    """단일 파서 시도 결과."""
    class_name: str = ""
    count: int = 0
    valid_count: int = 0
    error_count: int = 0
    errors: Dict[str, List[str]] = field(default_factory=dict)
    exception: Optional[str] = None


@dataclass
class FormatProfile:
    """PDF 포맷 프로파일 — 파서를 새로 개발할 때 참고하는 구조 서술.

    기존 파서 재사용 추천이 아니라, 이 기관 PDF의 포맷 특성을
    있는 그대로 서술하여 에이전트가 정확한 파서를 처음부터 작성할 수 있게 한다.
    """
    question_marker: str = "unknown"          # 가장 많이 탐지된 질문 마커
    total_row_marker: str = "unknown"         # 가장 많이 탐지된 전체 행 마커
    meta_cols: int = 0                        # 테이블 meta 컬럼 수
    ratio_location: str = "unknown"           # "table_cell" | "text_bundled" | "mixed"
    ratio_decimal_places: int = 1
    page_continuity: bool = False
    suggested_base_class: str = "_TableFormatParser"  # 코드 구조 참고용 (재사용 아님)
    key_challenges: List[str] = field(default_factory=list)   # 파서 개발 시 주의사항


@dataclass
class BasicInfo:
    """PDF 기본 정보."""
    page_count: int = 0
    text_extractable: bool = False
    cid_encoded: bool = False
    needs_gid_decode: bool = False
    file_size_bytes: int = 0


@dataclass
class PageInfo:
    """단일 페이지 분석 정보."""
    page_num: int = 0
    table_count: int = 0
    text_length: int = 0
    outside_text_length: int = 0
    cid_count: int = 0
    table_shapes: List[str] = field(default_factory=list)
    outside_text_sample: str = ""
    table_samples: List[List[List[Any]]] = field(default_factory=list)


@dataclass
class TextSamples:
    """텍스트 샘플 (에이전트 참고용)."""
    first_pages_text: List[str] = field(default_factory=list)   # 페이지별 전체 텍스트
    table_previews: List[Dict[str, Any]] = field(default_factory=list)  # 테이블 첫 5행


@dataclass
class ScreeningResult:
    """단일 PDF 스크리닝 결과 (JSON 출력 루트)."""
    schema_version: str = "1.0"
    generated_at: str = ""
    pdf_filename: str = ""
    pollster: str = ""
    pdf_path: str = ""

    basic_info: BasicInfo = field(default_factory=BasicInfo)
    question_block_patterns: QuestionBlockPatterns = field(default_factory=QuestionBlockPatterns)
    total_row_markers: TotalRowMarkers = field(default_factory=TotalRowMarkers)
    table_structure: TableStructure = field(default_factory=TableStructure)
    page_continuity: PageContinuity = field(default_factory=PageContinuity)
    parser_test_results: List[ParserTestResult] = field(default_factory=list)
    format_profile: FormatProfile = field(default_factory=FormatProfile)
    text_samples: TextSamples = field(default_factory=TextSamples)

    # 분석 오류
    error: Optional[str] = None


@dataclass
class PollsterProfile:
    """기관별 파서 개발 프로파일 (복수 PDF 공통 패턴 집약)."""
    schema_version: str = "1.0"
    generated_at: str = ""
    pollster: str = ""
    pdf_count: int = 0

    common_patterns: Dict[str, Any] = field(default_factory=dict)
    suggested_base_class: Optional[str] = None   # 코드 구조 참고용 (재사용 아님)
    key_challenges: List[str] = field(default_factory=list)
    per_pdf_screening_files: List[str] = field(default_factory=list)
