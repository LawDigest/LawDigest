"""여론조사 데이터 모델 (dataclass 정의)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ListRecord:
    """NESDC 목록 페이지의 단일 여론조사 레코드."""
    registration_number: str
    pollster: str
    sponsor: str
    method: str
    sample_frame: str
    title_region: str
    registered_date: str
    province: str
    detail_url: str
    ntt_id: Optional[str] = None


@dataclass
class MethodStats:
    """조사방법 세부 통계."""
    method_index: int
    method_name: str = ""
    method_share_percent: Optional[float] = None
    respondent_selection_method: str = ""
    target_population: str = ""
    sample_frame: str = ""
    frame_size: Optional[int] = None
    frame_build_method: str = ""
    sampling_method: str = ""
    notes: str = ""
    used_count: Optional[int] = None
    os_count: Optional[int] = None
    ne_count: Optional[int] = None
    u_count: Optional[int] = None
    r_count: Optional[int] = None
    i_count: Optional[int] = None
    total_count: Optional[int] = None
    contact_rate_percent: Optional[float] = None
    cooperation_rate_percent: Optional[float] = None


@dataclass
class PollDetail:
    """NESDC 상세 페이지에서 파싱한 여론조사 상세 정보."""
    source_url: str
    list_pollster: str = ""
    registration_number: str = ""
    election_type: str = ""
    region: str = ""
    election_name: str = ""
    sponsor: str = ""
    pollster: str = ""
    joint_pollster: str = ""
    surveyed_region: str = ""
    survey_datetimes: List[str] = field(default_factory=list)
    survey_duration: str = ""
    survey_target: str = ""
    sample_size_completed: Optional[int] = None
    sample_size_weighted: Optional[int] = None
    weighting_base_method: str = ""
    weighting_apply_method: str = ""
    extra_weighting_base_method: str = ""
    extra_weighting_apply_method: str = ""
    margin_of_error: str = ""
    publication_media_type: str = ""
    publication_media_name: str = ""
    first_publication_datetime: str = ""
    questionnaire_filename: str = ""
    questionnaire_download_url: str = ""
    analysis_filename: str = ""
    analysis_download_url: str = ""
    overall_landline_percent: Optional[float] = None
    overall_mobile_percent: Optional[float] = None
    overall_r_count: Optional[int] = None
    overall_i_count: Optional[int] = None
    overall_total_count: Optional[int] = None
    overall_contact_rate_percent: Optional[float] = None
    overall_response_rate_percent: Optional[float] = None
    methods: List[MethodStats] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class QuestionResult:
    """여론조사 결과표 PDF에서 파싱한 개별 설문 항목의 결과."""
    question_number: int
    question_title: str
    question_text: str
    response_options: List[str]
    overall_n_completed: Optional[int]
    overall_n_weighted: Optional[int]
    overall_percentages: List[float]


@dataclass
class PollResultSet:
    """한 여론조사의 결과표 PDF에서 추출한 전체 결과."""
    registration_number: str
    source_url: str
    pdf_path: str
    questions: List[QuestionResult] = field(default_factory=list)
