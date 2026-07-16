import json
import subprocess
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def disable_agentic_prefetch_network(monkeypatch):
    monkeypatch.setattr(
        "lawdigest_ai.processor.agentic_bill_report._build_open_assembly_client",
        lambda api_key=None: None,
    )


def _model_context(prompt: str) -> str:
    from lawdigest_ai.processor.agentic_bill_report import REPORT_SKILL_BODY

    return f"{REPORT_SKILL_BODY}\n{prompt}"


def test_agentic_report_prompt_uses_prefetched_evidence():
    from lawdigest_ai.processor.agentic_bill_report import REPORT_SKILL_NAME, build_bill_report_prompt

    prompt = build_bill_report_prompt(
        {
            "bill_id": "PRC_TEST",
            "bill_number": "2206772",
            "bill_name": "인공지능 발전과 신뢰 기반 조성 등에 관한 기본법안",
            "summary": "인공지능 산업 진흥 및 신뢰 기반 조성",
            "bill_result": "원안가결",
            "stage": "공포",
            "propose_date": "2024-11-01",
            "proposers": "홍길동의원 등 10인",
            "committee": "과학기술정보방송통신위원회",
        }
    )
    context = _model_context(prompt)

    assert prompt.startswith(f"${REPORT_SKILL_NAME}")
    assert "deterministic evidence packet" in prompt
    assert "제공된 evidence 안에서만 사실관계를 사용" in prompt
    assert "이미 통과된 법안" not in prompt
    assert "MCP 도구를 능동적으로 사용" not in prompt
    assert "추가 도구 호출, 웹 검색, 셸 명령 실행을 하지 말고" in prompt
    assert "bill_text, current_law, committee_materials, cost_estimate" in context
    assert "lifecycle, 현재 심사 단계, 처리 상태처럼 시간이 지나며 바뀌는 정보" in context
    assert "open_assembly.fetch_bill_detail" in prompt
    assert "open_assembly.fetch_bill_summary" in prompt
    assert "open_assembly.fetch_bill_lifecycle" not in prompt


def test_agentic_report_prompt_targets_user_facing_report(monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import build_bill_report_prompt

    monkeypatch.delenv("LAW_OC", raising=False)

    prompt = build_bill_report_prompt(
        {
            "bill_id": "PRC_TEST",
            "bill_number": "2206772",
            "bill_name": "테스트법 일부개정법률안",
            "summary": "테스트 요약",
            "bill_result": "원안가결",
            "stage": "공포",
        }
    )
    context = _model_context(prompt)

    assert "사용자에게 보여줄 최종 법안 리포트" in prompt
    assert "쉬운 요약" in context
    assert "쉬운 말로 충분히 설명" in context
    assert "5개 불릿" in context
    assert "리포트 모드: deep_report" in prompt
    assert "6,000~8,000자 안팎" in context
    assert "**항목 제목**: 쉬운 설명" in context
    assert "**부당한 표시·광고 제한**: 허위·과장 등 소비자를 오도할 수 있는 표현을 규제해요." in context
    assert "Lawdigest 요약 개선 제안" not in prompt
    assert "사용한 MCP 도구와 출처" not in prompt
    assert "내부 조사 로그" in prompt
    assert "추가 도구 호출" in prompt
    assert "현재 심사 단계" in context
    assert "아직 법으로 확정된 건 아니고" not in prompt
    assert "처리 상태" in context
    assert "하기 위한 법률 개정안이에요" in context
    assert "title은 카드용 제목형 요약" in prompt
    assert "원문 첫 문장을 복사하지 말고" in prompt
    assert "'[핵심 변경 목적/수단]을/를 위한 [정확한 bill.bill_name]'" in prompt
    assert "괄호 설명이나 설명 불릿으로 끼워 넣지 마세요" in context
    assert "어려운 법률·행정용어" in context
    assert '"legal_terms"' in context
    assert "원문 요약:" in context
    assert "쉬운 풀이:" in context
    assert "후처리" in context
    assert "툴팁 문법" in context
    assert "설명 불릿으로 끼워 넣지 마세요" in context
    assert "해요체" in context
    assert "자연스러운 단어로만 쓰세요" in context
    assert "고정 접두어를 반복하지 마세요" in context
    assert "고정 접두어 없이" in context
    assert "### 1) 제목" in context
    assert "제목, 원문 요약 문단, 설명/풀이 불릿" in context
    assert "원문 요약 문단은 2문장" in context
    assert "2~3개 불릿" in context
    assert "불릿만으로 변화 묶음을 시작하지 마세요" in context
    assert "짧은 명사형 항목명" in context
    assert "허위개발정보 유포를 금지하는 조문 신설" in context
    assert "인터넷 표시·광고의 필수정보와 부당한 표시를 제한" in context
    assert "행정문서식 표현은 피하고" in context
    assert "**중요 단어**" in context
    assert "<mark>중요 문장</mark>" in context
    assert "자연스러운 `-요` 체" in context
    assert "`합니다`, `됩니다`, `입니다`, `바뀝니다`" in context
    assert "짧게 쓴다는 이유로 근거, 영향, 예외를 덜어내지 마세요" in context
    assert "법률·행정용어 풀이 사전" in prompt
    assert "정적 보조 사전" in prompt
    assert "target=lstrm" in prompt
    assert "target=lstrmAI" not in prompt
    assert "target=lstrmRlt" not in prompt
    assert "{{용어:뜻}}" not in context
    assert "설명하지 않을 용어" in prompt


def test_build_bill_report_evidence_prefetches_effective_open_assembly_rows(monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import build_bill_report_evidence

    monkeypatch.delenv("LAW_OC", raising=False)
    calls = []

    class FakeClient:
        def fetch_bill_detail(self, bill_id):
            calls.append(("detail", bill_id))
            return {
                "BILL_ID": bill_id,
                "BILL_NO": "2212345",
                "BILL_NM": "테스트법 일부개정법률안",
                "BILL_PDF_URL": "https://example.test/bill.pdf",
            }

        def fetch_bill_summary(self, bill_no):
            calls.append(("summary", bill_no))
            return {
                "BILL_NO": bill_no,
                "SUMMARY": "제안이유 및 주요내용 현행법 제12조를 고쳐 비용추계 미첨부 사유를 명확히 하려는 원문 요약",
            }

        def fetch_rows(self, endpoint, params, *, all_pages, page_size):
            calls.append(("rows", endpoint, params, all_pages, page_size))
            return [
                {
                    "BILL_ID": "PRC_PREFETCH",
                    "BILL_NO": params["BILL_NO"],
                    "REPORT_NM": "검토보고서",
                    "ETC": "비용추계 미첨부 사유서 포함",
                },
                {"BILL_ID": "PRC_OTHER", "BILL_NO": "9999999", "REPORT_NM": "다른 법안 검토보고서"},
            ]

    monkeypatch.setattr(
        "lawdigest_ai.processor.agentic_bill_report._build_open_assembly_client",
        lambda api_key=None: FakeClient(),
    )

    evidence = build_bill_report_evidence(
        {
            "bill_id": "PRC_PREFETCH",
            "bill_number": "",
            "bill_name": "테스트법 일부개정법률안",
            "bill_result": "원안가결",
        }
    )

    assert evidence["report_mode"] == "deep_report"
    assert evidence["prefetch_errors"] == []
    assert evidence["open_assembly"]["detail"]["BILL_NO"] == "2212345"
    assert "비용추계 미첨부 사유" in evidence["open_assembly"]["summary"]["SUMMARY"]
    assert "lifecycle" not in evidence["open_assembly"]
    assert "현행법 제12조" in evidence["bill_text"]["proposal_reason_and_major_content"]
    assert evidence["bill_text"]["target_law_names"] == ["테스트법"]
    assert evidence["bill_text"]["mentioned_articles"] == [{"label": "제12조", "JO": "001200"}]
    assert evidence["current_law"]["target_law_names"] == ["테스트법"]
    assert evidence["current_law"]["laws"][0]["status"] == "law_api_unavailable"
    assert evidence["open_assembly"]["review"] == [
        {
            "BILL_ID": "PRC_PREFETCH",
            "BILL_NO": "2212345",
            "REPORT_NM": "검토보고서",
            "ETC": "비용추계 미첨부 사유서 포함",
        }
    ]
    assert evidence["committee_materials"]["status"] == "found"
    assert evidence["cost_estimate"]["status"] == "found"
    assert "법률·행정용어 풀이 사전" in evidence["legal_terms"]["context"]
    assert calls == [
        ("detail", "PRC_PREFETCH"),
        ("summary", "2212345"),
        ("rows", "BILLJUDGE", {"BILL_NO": "2212345"}, False, 10),
    ]


def test_agentic_report_prompt_summary_mode_aliases_to_deep_report_contract():
    from lawdigest_ai.processor.agentic_bill_report import REPORT_SKILL_NAME, build_bill_report_prompt

    prompt = build_bill_report_prompt(
        {
            "bill_id": "PRC_PENDING",
            "bill_number": "2219999",
            "bill_name": "접수 테스트법안",
            "summary": "막 접수된 법안 요약",
            "bill_result": "접수",
            "stage": "소관위접수",
        },
        report_mode="summary",
    )
    context = _model_context(prompt)

    assert prompt.startswith(f"${REPORT_SKILL_NAME}")
    assert "리포트 모드: deep_report" in prompt
    assert "모든 법안은 처리 상태와 관계없이 긴 버전 리포트" in prompt
    assert "아직 통과되지 않았거나 막 접수된 법안" in prompt
    assert "1,500~2,500자 안팎" not in prompt
    assert "6,000~8,000자 안팎" in context


def test_agentic_report_batch_prompt_isolates_bill_reports():
    from lawdigest_ai.processor.agentic_bill_report import REPORT_SKILL_BODY, REPORT_SKILL_NAME, build_bill_report_batch_prompt

    prompt = build_bill_report_batch_prompt([
        {
            "bill_id": "PRC_BATCH_1",
            "bill": {"bill_id": "PRC_BATCH_1", "bill_name": "배치 테스트법안 1"},
            "report_mode": "deep_report",
            "evidence": {"db_bill": {"summary": "첫 번째 근거"}},
        },
        {
            "bill_id": "PRC_BATCH_2",
            "bill": {"bill_id": "PRC_BATCH_2", "bill_name": "배치 테스트법안 2"},
            "report_mode": "deep_report",
            "evidence": {"db_bill": {"summary": "두 번째 근거"}},
        },
    ])
    context = _model_context(prompt)

    assert prompt.startswith(f"${REPORT_SKILL_NAME}")
    assert "각 항목은 서로 완전히 독립된 작업" in prompt
    assert "다른 법안 리포트에 절대 옮기지 마세요" in prompt
    assert "JSON 객체 하나만 작성하세요" in prompt
    assert '"reports"' in prompt
    assert '"title"' in prompt
    assert '"report_body"' in prompt
    assert '{"reports":[{"title"' in prompt
    assert '"bill_id":"PRC_EXAMPLE"' not in prompt
    assert "처리 상태와 관계없이 deep_report 긴 버전" in prompt
    assert "같은 순서로 title과 report_body" in prompt
    assert "### 1) 제목" in context
    assert "번호 헤딩 다음에는 불릿이 아닌 일반 문단" in context
    assert "## 배치 출력" not in REPORT_SKILL_BODY
    assert "JSON 객체 하나만 작성하세요" in REPORT_SKILL_BODY


def test_agentic_report_validation_rejects_internal_tool_leaks():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 확인한 근거
- open-assembly `get_bill_detail`
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "내부 조사 표현" in str(exc)
    else:
        raise AssertionError("내부 도구명이 섞인 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_generic_term_label():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나
- 기존 법의 제23조는 청문 요건만 두고 있었습니다.
  - 용어 설명: 청문은 처분 전에 의견을 낼 수 있는 절차입니다.
  - 쉽게 말하면, 사후 처분 중심에서 예방 단계 관리로 바뀝니다.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "내부 조사 표현" in str(exc)
    else:
        raise AssertionError("용어 설명 메타 라벨이 섞인 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_original_summary_label():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나
- 원문 요약: 기존 조문에 새 규정이 추가됩니다.
  - 과태료: 행정질서 위반에 대한 금전 제재입니다.
  - 쉽게 말하면, 규칙을 어기면 비용 부담이 생깁니다.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "내부 조사 표현" in str(exc)
    else:
        raise AssertionError("원문 요약 메타 라벨이 섞인 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_easy_explanation_label():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
- 기존 조문에 새 규정이 추가됩니다.
  쉬운 풀이: 사용자가 거래 전에 정보를 더 확인할 수 있게 됩니다.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "내부 조사 표현" in str(exc)
    else:
        raise AssertionError("쉬운 풀이 메타 라벨이 섞인 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_malformed_term_tooltip():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**거래 전 정보 확인**을 더 쉽게 만들기 위한 법률 개정안이에요.
<mark>핵심 변화는 거래 전 확인 절차가 더 분명해지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 의견 확인 절차 정비

기존 제도는 {{청문:처분 전에 의견을 듣는 절차를 더 분명히 두고 있어요.

- 사용자 입장에서는, 처분 전에 의견을 말할 기회가 더 선명해져요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "툴팁 표기" in str(exc)
    else:
        raise AssertionError("깨진 툴팁 표기는 성공하면 안 됩니다.")


def test_agentic_report_validation_does_not_require_hardcoded_term_tooltip():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**거래 전 정보 확인**을 더 쉽게 만들기 위한 법률 개정안이에요.
<mark>핵심 변화는 과태료 부과 기준이 더 분명해지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 금전 제재 기준 정비

기존 제도는 과태료 부과 근거를 두고 있었고, 제안안은 적용 기준을 더 분명히 해요.

- 사용자 입장에서는, 어떤 위반에 비용 부담이 생기는지 더 알기 쉬워져요.
"""

    _validate_report_body(report_body)


def test_agentic_report_repair_does_not_insert_hardcoded_term_tooltip():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이에요.</mark>

## 주요 내용
- 지원 근거: 설명이에요.

## 무엇이 달라지나

### 1) 과태료 부과 기준 정비

과태료 기준을 더 분명하게 정해요.

사용자 입장에서는, 어떤 위반에 비용 부담이 생기는지 더 알기 쉬워져요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "- **지원 근거**: 설명이에요." in repaired
    assert "{{과태료:" not in repaired
    assert "- 사용자 입장에서는," in repaired
    _validate_report_body(repaired)


def test_agentic_report_postprocess_strips_tooltips_without_agent_decision():
    from lawdigest_ai.processor.agentic_bill_report import _postprocess_report_body, _validate_report_body

    report_body = """
# 청문 절차 정비법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 청문 절차가 더 분명해지는 점이에요.</mark>

## 주요 내용
- **지원 근거**: 청문 절차를 정비해요.

## 무엇이 달라지나

### 1) 의견 확인 절차 정비

처분 전에 청문 절차를 거치도록 해 의견을 말할 기회를 더 분명히 해요.

- 사용자 입장에서는, 어떤 절차와 책임이 달라지는지 더 알기 쉬워져요.
""".strip()

    postprocessed = _postprocess_report_body(report_body)

    assert postprocessed.startswith("# 청문 절차 정비법 일부개정법률안")
    assert "{{청문" not in postprocessed.splitlines()[0]
    assert "{{청문" not in postprocessed
    _validate_report_body(postprocessed)


def test_agentic_report_postprocess_unwraps_single_report_json_before_tooltip_injection():
    from lawdigest_ai.processor.agentic_bill_report import _postprocess_report_body, _validate_report_body

    report_body = """
# 청문 절차 정비법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 청문 절차가 더 분명해지는 점이에요.</mark>

## 주요 내용
- **지원 근거**: 청문 절차를 정비해요.

## 무엇이 달라지나

### 1) 의견 확인 절차 정비

처분 전에 청문 절차를 거치도록 해 의견을 말할 기회를 더 분명히 해요.

- 사용자 입장에서는, 어떤 절차와 책임이 달라지는지 더 알기 쉬워져요.
""".strip()
    wrapped = json.dumps({"reports": [{"report_body": report_body}]}, ensure_ascii=False)

    postprocessed = _postprocess_report_body(
        wrapped,
        bill={"bill_id": "PRC_JSON_WRAP", "bill_name": "청문 절차 정비법 일부개정법률안"},
    )

    assert postprocessed.startswith("# 청문 절차 정비법 일부개정법률안")
    assert not postprocessed.lstrip().startswith("{")
    assert "{{청문" not in postprocessed
    _validate_report_body(postprocessed)


def test_agentic_report_applies_high_confidence_tooltip_decisions_only():
    from lawdigest_ai.processor.agentic_bill_report import (
        _apply_legal_term_tooltip_decisions,
        _parse_legal_term_tooltip_decisions,
    )
    from lawdigest_ai.processor.legal_term_glossary import LegalTermEntry

    report_body = """
# 청문 절차 정비법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 청문 절차가 더 분명해지는 점이에요.</mark>

## 주요 내용
- **지원 근거**: 청문 절차를 정비해요.

## 무엇이 달라지나

### 1) 의견 확인 절차 정비

처분 전에 청문 절차를 거치도록 해 의견을 말할 기회를 더 분명히 해요.

- 사용자 입장에서는, 어떤 절차와 책임이 달라지는지 더 알기 쉬워져요.
""".strip()
    candidates = [
        LegalTermEntry(term="청문", definition="처분 전에 당사자의 의견을 듣는 절차예요.", aliases=("청문", "청문 절차")),
        LegalTermEntry(term="정확성", definition="위성서비스에서 위치가 맞는 정도를 말해요.", aliases=("정확성",)),
        LegalTermEntry(
            term="불법어업",
            definition=(
                "연근해어업에 종사하는 어선 또는 외국어선(대한민국의 관할 수역에서 연근해어업에 종사하는 외국어선으로 한정한다. 이하 같다)이 "
                "국내법을 위반하여 행하는 어업활동 또는 "
                "조약이나 국제적 협약ㆍ협정 등에서 정하고 있는 수산자원 관리 기준을 위반하여 행하는 어업활동을 말해요."
            ),
            aliases=("불법어업",),
        ),
        LegalTermEntry(term="생산성", definition="부가가치를 만드는 정도를 말해요.", aliases=("생산성",)),
    ]
    decisions_json = json.dumps(
        {
            "tooltips": [
                {
                    "term": "청문",
                    "surface": "청문 절차",
                    "definition": "에이전트가 바꾼 정의는 쓰면 안 돼요.",
                    "reason": "이 법안의 핵심 절차 용어예요.",
                    "confidence": "high",
                },
                {
                    "term": "정확성",
                    "surface": "정확성",
                    "definition": "위성서비스에서 위치가 맞는 정도를 말해요.",
                    "reason": "일반어라 불확실해요.",
                    "confidence": "low",
                },
                {
                    "term": "불법어업",
                    "surface": "불법어업",
                    "definition": "긴 정의도 에이전트가 골랐어요.",
                    "reason": "사전 정의가 너무 길면 주입하지 않아야 해요.",
                    "confidence": "high",
                },
                {
                    "term": "생산성",
                    "surface": "생산성",
                    "definition": "일반어도 에이전트가 골랐어요.",
                    "reason": "문맥 정의가 빗나가기 쉬운 일반어예요.",
                    "confidence": "high",
                },
            ],
            "rejected": [],
        },
        ensure_ascii=False,
    )

    decisions = _parse_legal_term_tooltip_decisions(decisions_json, candidates)
    rendered = _apply_legal_term_tooltip_decisions(report_body, decisions)

    assert "{{청문 절차:처분 전에 당사자의 의견을 듣는 절차예요.}}" in rendered
    assert "에이전트가 바꾼 정의" not in rendered
    assert "{{정확성:" not in rendered
    assert "{{불법어업:" not in rendered
    assert "{{생산성:" not in rendered
    assert [decision.term for decision in decisions] == ["청문"]


def test_agentic_report_repair_inserts_mark_inside_bullet():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body

    repaired = _repair_report_body(
        "# 테스트법안\n\n"
        "## 쉬운 요약\n"
        "- **핵심 변화**는 절차가 더 분명해지는 점이에요.\n\n"
        "## 주요 내용\n"
        "- **지원 근거**: 설명이에요.\n\n"
        "## 무엇이 달라지나\n\n"
        "### 1) 절차 정비\n\n"
        "절차를 더 분명하게 정리해요.\n"
    )

    assert "- <mark>**핵심 변화**는 절차가 더 분명해지는 점이에요.</mark>" in repaired
    assert "<mark>-" not in repaired


def test_agentic_report_validation_accepts_dictionary_term_tooltip():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이에요.</mark>

## 주요 내용
- **지원 근거**: 설명이에요.

## 무엇이 달라지나

### 1) 의견 확인 절차 정비

처분 전에 {{청문 절차:처분을 하기 전에 당사자의 의견을 듣는 절차}}를 거치도록 해 의견을 말할 기회를 더 분명히 해요.

- 사용자 입장에서는, 어떤 절차와 책임이 달라지는지 더 알기 쉬워져요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "{{청문 절차:" in repaired
    _validate_report_body(repaired)


def test_agentic_report_repair_dedupes_adjacent_same_term_tooltip():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**공유재산{{공유재산:지방자치단체 소유 재산을 말해요.}} 관리 기준을 정비하기 위한 법률 개정안이에요.**
<mark>핵심 변화는 {{변상금:무단 점유자에게 부과하는 금액을 말해요.}} 조정 근거가 넓어지는 점이에요.</mark>

## 주요 내용
- **지원 근거**: 설명이에요.

## 무엇이 달라지나

### 1) 금액 조정 근거 정비

공유재산{{공유재산:지방자치단체 소유 재산을 말해요.}}을 주거 목적으로 점유한 경우 예외를 둘 수 있게 해요.

- 사용자 입장에서는, 생활 회복을 막는 부담을 줄일 여지가 생겨요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "공유재산{{공유재산:" not in repaired
    assert repaired.count("{{공유재산:") == 1
    assert "공유재산을 주거 목적으로" in repaired
    _validate_report_body(repaired)


def test_agentic_report_repair_keeps_only_first_tooltip_per_term():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
- <mark>{{인공지능기술:인공지능을 구현하기 위한 기술을 말해요.}}을 쓰는 행정 결정을 설명받기 쉽게 하는 법률 개정안이에요.</mark>

## 주요 내용
- **설명 기준**: 행정청이 인공지능기술을 쓴 결정을 설명하는 기준을 더 분명하게 해요.

## 왜 나왔나
행정이 {{인공지능기술:인공지능을 구현하기 위한 기술을 말해요.}}을 쓰면 결과가 빠르게 나오지만 이유를 알기 어려울 수 있어요.

## 무엇이 달라지나

### 1) 설명 요구 기준 정비

행정청이 **설명 기준**을 더 분명하게 마련해요.

- 사용자는 결정 이유를 더 쉽게 확인할 수 있어요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert repaired.count("{{인공지능기술:") == 1
    assert "행정이 인공지능기술을 쓰면" in repaired
    _validate_report_body(repaired)


def test_agentic_report_repair_simplifies_hard_change_headings():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
- <mark>핵심 변화는 **숙소 기준**을 더 쉽게 확인하게 하는 점이에요.</mark>

## 주요 내용
- **숙소 기준**: 안전하지 않은 숙소를 줄이고 필요한 지원을 늘려요.

## 왜 나왔나
현장에서 기준을 지키기 어려운 경우가 있어서 나온 법안이에요.

## 무엇이 달라지나

### 1) 안전한 숙소 확충 유도

지원 근거를 두어 **안전한 숙소**를 늘리려는 내용이에요.

- 사용자 입장에서는 살 곳의 기준을 더 쉽게 확인할 수 있어요.

### 2) 지역장애인권익옹호기관 확충

지역별로 **도움받을 곳**을 더 가까이 두려는 내용이에요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "### 1) 안전한 숙소 늘리기" in repaired
    assert "### 2) 지역장애인권익옹호기관 늘리기" in repaired
    assert "확충" not in repaired
    _validate_report_body(repaired)


def test_agentic_report_repair_fixes_term_tooltip_particles():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
- **공유재산{{공유재산:지방자치단체 소유 재산을 말해요.}}를 주거 목적으로 점유한 취약계층을 더 배려하기 위한 법률 개정안이에요.**
- <mark>핵심 변화는 변상금{{변상금:무단 점유자에게 부과하는 금액을 말해요.}}를 조정할 수 있는 근거를 넓히는 점이에요.</mark>

## 주요 내용
- **지원 근거**: 설명이에요.

## 무엇이 달라지나

### 1) 금액 조정 근거 정비

공유재산{{공유재산:지방자치단체 소유 재산을 말해요.}}를 주거 목적으로 점유한 경우 예외를 둘 수 있게 해요.

- 사용자 입장에서는, 생활 회복을 막는 부담을 줄일 여지가 생겨요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "{{공유재산:지방자치단체 소유 재산을 말해요.}}을 주거 목적으로" in repaired
    assert "{{변상금:무단 점유자에게 부과하는 금액을 말해요.}}을 조정" in repaired
    assert "공유재산{{공유재산:" not in repaired
    assert "변상금{{변상금:" not in repaired
    _validate_report_body(repaired)


def test_agentic_report_repair_adds_missing_highlight():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
- **거래 전 정보 확인**을 더 쉽게 만들기 위한 법률 개정안이에요.

## 주요 내용
- **지원 근거**: 설명이에요.

## 무엇이 달라지나

### 1) 정보 제공 기준 정비

거래 전 단계에서 **정보 제공 기준**을 더 분명하게 해요.

- 사용자가 확인해야 할 내용을 더 빨리 볼 수 있어요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "<mark>" in repaired
    _validate_report_body(repaired)


def test_agentic_report_repair_moves_bullet_marker_outside_highlight():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
- **거래 전 정보 확인**을 더 쉽게 만들기 위한 법률 개정안이에요.
<mark>- 핵심 변화는 **거래 전 정보 확인**이 쉬워지는 점이에요.</mark>

## 주요 내용
- **지원 근거**: 설명이에요.

## 무엇이 달라지나

### 1) 정보 제공 기준 정비

거래 전 단계에서 **정보 제공 기준**을 더 분명하게 해요.

- 사용자가 확인해야 할 내용을 더 빨리 볼 수 있어요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "<mark>-" not in repaired
    assert "- <mark>핵심 변화는 **거래 전 정보 확인**이 쉬워지는 점이에요.</mark>" in repaired
    _validate_report_body(repaired)


def test_agentic_report_repair_converts_html_bold_inside_highlight():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
- <mark><strong>장애인학대</strong> 예방 체계를 더 촘촘하게 만들기 위한 법률 개정안이에요.</mark>

## 주요 내용
- **지원 근거**: 설명이에요.

## 무엇이 달라지나

### 1) 지원 기준 정비

지역에서 **도움받을 곳**을 더 쉽게 찾게 해요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "<strong>" not in repaired
    assert "<mark>**장애인학대** 예방 체계를 더 촘촘하게 만들기 위한 법률 개정안이에요.</mark>" in repaired
    _validate_report_body(repaired)


def test_agentic_report_repair_adds_missing_bold_keyword():
    from lawdigest_ai.processor.agentic_bill_report import _repair_report_body, _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
- 거래 전 정보 확인을 더 쉽게 만들기 위한 법률 개정안이에요.
<mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- 지원 근거를 더 분명하게 해요.

## 무엇이 달라지나

### 1) 정보 제공 기준 정비

거래 전 단계에서 정보 제공 기준을 더 분명하게 해요.

- 사용자가 확인해야 할 내용을 더 빨리 볼 수 있어요.
""".strip()

    repaired = _repair_report_body(report_body)

    assert "**거래 전 정보 확인**" in repaired
    _validate_report_body(repaired)


def test_agentic_report_validation_ignores_source_section_legal_terms():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 허위정보 유포 금지 조문 신설

제23조의2를 새로 둬 **허위정보 유포**를 금지해요.

- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.

## 확인한 근거
- 법제처: 제23조(청문), 제25조의3(권한 등의 위임 및 위탁), 제28조(과태료)
"""

    _validate_report_body(report_body)


def test_agentic_report_validation_requires_numbered_change_headings():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
- 제23조의2를 새로 둬 허위정보 유포를 금지합니다.
  - 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "번호 헤딩" in str(exc)
    else:
        raise AssertionError("번호 헤딩 없는 변화 설명은 성공하면 안 됩니다.")


def test_agentic_report_validation_accepts_numbered_change_heading_format():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 허위개발정보 유포를 금지하는 조문 신설

허위 개발정보 등으로 부동산 거래를 유인하는 행위를 직접 금지하는 조문이 추가돼요.

- 확인되지 않은 자극적 정보가 그대로 퍼져 피해를 주는 구조가 줄어들어요.

### 2) 신고내용조사 위탁 범위 확대

제25조의3에 제3항을 추가해 신고내용조사 관련 권한 {{위임·위탁:행정기관이 가진 권한이나 업무 일부를 다른 기관이 맡아 처리하게 하는 방식}} 근거를 넓혀요.

- 지방정부가 신고자료 검증을 더 빠르게 처리할 수 있어요.
"""

    _validate_report_body(report_body)


def test_agentic_report_validation_accepts_term_tooltips():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 신고내용조사 위탁 범위 확대

제25조의3에 제3항을 추가해 신고내용조사 관련 권한 {{위임·위탁:행정기관이 가진 권한이나 업무 일부를 다른 기관이 맡아 처리하게 하는 방식}} 근거를 넓혀요.

- 지방정부가 신고자료 검증을 더 빠르게 처리할 수 있어요.

### 2) 위반 시 금전 제재 강화

허위정보와 부당광고를 어기면 {{과태료:행정질서 위반에 부과하는 금전 제재}} 부과 대상이 더 분명해져요.

- 반복 위반을 더 빠르게 제재할 수 있어요.
"""

    _validate_report_body(report_body)


def test_agentic_report_validation_rejects_unbolded_colon_labels():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- 권한 정비: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 허위정보 유포 금지 조문 신설

제23조의2를 새로 둬 **허위정보 유포**를 금지해요.

- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "콜론 앞 핵심 라벨" in str(exc)
    else:
        raise AssertionError("콜론 앞 핵심 라벨이 볼드체가 아닌 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_hard_change_headings():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 벌칙·과태료 체계 개정과 집행주체 확충

허위정보와 부당광고를 어기면 {{과태료:행정질서 위반에 부과하는 금전 제재}} 등 **제재**가 더 분명해져요.

- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "쉬운 변화 제목" in str(exc)
    else:
        raise AssertionError("어려운 행정식 변화 제목은 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_missing_visual_emphasis():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약이에요.

## 주요 내용
- 권한 정비: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 허위정보 유포 금지 조문 신설

제23조의2를 새로 둬 허위정보 유포를 금지해요.

- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "볼드체" in str(exc)
    else:
        raise AssertionError("중요 단어 볼드체가 없는 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_missing_highlight():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요.

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 허위정보 유포 금지 조문 신설

제23조의2를 새로 둬 **허위정보 유포**를 금지해요.

- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "하이라이트" in str(exc)
    else:
        raise AssertionError("중요 문장 하이라이트가 없는 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_formal_tone():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 허위정보 유포 금지 조문 신설

제23조의2를 새로 둬 **허위정보 유포**를 금지합니다.

- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "-요 체" in str(exc)
    else:
        raise AssertionError("격식체 종결이 남은 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_awkward_yo_tone():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 허위정보 유포 금지 조문 신설

제23조의2를 새로 둬 **허위정보 유포**를 금지해요.

- 피해 가능성이 줄어드어요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "어색한 -요 체" in str(exc)
    else:
        raise AssertionError("어색한 -요 체가 남은 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_rejects_sentence_style_change_headings():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나

### 1) 허위정보 유포 금지 조문을 새로 둔다

제23조의2를 새로 둬 허위정보 유포를 금지합니다.

- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "명사형 제목" in str(exc)
    else:
        raise AssertionError("문장형 변화 제목은 성공하면 안 됩니다.")


def test_agentic_report_validation_allows_term_explanation_without_hardcoded_vocab_blocklist():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**거래 전 정보 확인**을 더 쉽게 만들기 위한 법률 개정안이에요.
<mark>핵심 변화는 정보 유통 단계의 책임이 더 분명해지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 정보 유통 책임 정비

제23조의2를 새로 둬 **허위정보 유포**를 금지해요.

- 허위정보는 거래를 성사시키기 위해 사실이 아닌 내용으로 유포된 광고·글·영상·이미지를 말해요.
- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    _validate_report_body(report_body)


def test_legal_term_glossary_context_uses_static_fallback_without_law_open_api(monkeypatch):
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

    monkeypatch.delenv("LAW_OC", raising=False)

    context = build_legal_term_glossary_context("청문 규정과 과태료, 허위정보 유포를 설명합니다.")

    assert "법률·행정용어 풀이 사전" in context
    assert "정적 보조 사전" in context
    assert "법제처 API 조회 결과" not in context
    assert "lawSearch.do?target=lstrm" in context
    assert "lawService.do?target=lstrm" in context
    assert "lawService.do?target=lstrmRlt" not in context
    assert "lawService.do?target=dlytrmRlt" not in context
    assert "청문 규정: 처분을 받기 전에" in context
    assert "과태료: 행정질서 위반" in context
    assert "허위정보" in context
    assert "설명하지 않을 용어" in context


def test_legal_term_glossary_context_includes_real_api_lookup_results():
    from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTerm
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

    class FakeTermClient:
        enabled = True

        def lookup_term(self, query):
            return LawOpenApiTerm(
                term=query,
                source="law.go.kr",
                definitions=("처분 전에 당사자의 의견을 직접 듣고 증거를 조사하는 절차를 말한다.",),
            )

    context = build_legal_term_glossary_context("청문 규정을 설명합니다.", term_client=FakeTermClient())

    assert "아래 `법제처 용어사전 조회 결과`" in context
    assert "설명할 용어:" in context
    assert "청문: 처분 전에 당사자의 의견을 직접 듣고 증거를 조사하는 절차를 말한다." in context
    assert "일상어 연계어" not in context
    assert "청문 규정: 처분을 받기 전에" in context


def test_legal_term_glossary_context_prefers_local_dictionary(monkeypatch):
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context
    from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTerm

    monkeypatch.setattr(
        "lawdigest_ai.processor.legal_term_glossary._lookup_local_dictionary_terms",
        lambda terms: [
            LawOpenApiTerm(
                term="결격사유",
                source="lawdigest-local-dictionary",
                definitions=("로컬 사전에 저장된 결격사유 정의입니다.",),
            )
        ],
    )

    api_calls = []

    class FakeTermClient:
        enabled = True

        def lookup_term(self, query):
            api_calls.append(query)
            return None

    context = build_legal_term_glossary_context("임원의 결격사유를 정비합니다.", term_client=FakeTermClient())

    assert "결격사유" not in api_calls
    assert "결격사유: 로컬 사전에 저장된 결격사유 정의입니다." in context


def test_legal_term_glossary_context_extracts_defined_terms_from_bill_text():
    from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTerm
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

    class FakeTermClient:
        enabled = True

        def lookup_term(self, query):
            if query == "공유재산":
                return LawOpenApiTerm(
                    term=query,
                    source="law.go.kr",
                    definitions=("지방자치단체 소유로 된 재산을 말한다.",),
                )
            return None

    context = build_legal_term_glossary_context(
        "현행법은 공유재산을 무단점유한 자에게 변상금을 징수하도록 하고 있습니다.",
        term_client=FakeTermClient(),
    )

    assert "공유재산: 지방자치단체 소유로 된 재산을 말한다." in context
    assert "일상어 연계어" not in context
    assert "청문 규정: 처분을 받기 전에" not in context


def test_legal_term_glossary_context_uses_law_api_as_candidate_filter():
    from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTerm
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

    calls = []

    class FakeTermClient:
        enabled = True

        def lookup_term(self, query):
            calls.append(query)
            if query == "결격사유":
                return LawOpenApiTerm(
                    term=query,
                    source="law.go.kr",
                    definitions=("일정한 자격을 가질 수 없게 하는 법정 사유를 말한다.",),
                )
            return None

    context = build_legal_term_glossary_context(
        "기관 임원의 결격사유와 등록취소 절차를 정비합니다.",
        term_client=FakeTermClient(),
    )

    assert "결격사유" in calls
    assert "결격사유: 일정한 자격을 가질 수 없게 하는 법정 사유를 말한다." in context


def test_legal_term_glossary_context_ignores_api_results_without_definitions():
    from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTerm
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

    class FakeTermClient:
        enabled = True

        def lookup_term(self, query):
            return LawOpenApiTerm(
                term=query,
                source="law.go.kr",
                related_daily_terms=("면담", "심문"),
            )

    context = build_legal_term_glossary_context("청문 규정을 설명합니다.", term_client=FakeTermClient())

    assert "정적 보조 사전" in context
    assert "법제처 API 조회 결과" not in context
    assert "일상어 연계어" not in context


def test_legal_term_glossary_context_ignores_english_only_definitions():
    from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTerm
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

    class FakeTermClient:
        enabled = True

        def lookup_term(self, query):
            return LawOpenApiTerm(
                term=query,
                source="law.go.kr",
                definitions=("A hearing is an administrative procedure.",),
            )

    context = build_legal_term_glossary_context("결격사유를 설명합니다.", term_client=FakeTermClient())

    assert "A hearing is an administrative procedure." not in context
    assert "법제처 용어사전 조회 결과" not in context


def test_legal_term_glossary_context_skips_obvious_common_terms_in_api_candidates():
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

    calls = []

    class FakeTermClient:
        enabled = True

        def lookup_term(self, query):
            calls.append(query)
            return None

    context = build_legal_term_glossary_context("허위정보 유포를 설명합니다.", term_client=FakeTermClient())

    assert "허위정보" not in calls
    assert "허위정보 유포" not in calls
    assert "정적 보조 사전" in context
    assert "법제처 API 조회 결과" not in context
    assert "청문 규정: 처분을 받기 전에" in context


def test_agentic_report_validation_rejects_repeated_easy_explanation_starter():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
- 기존 제28조는 {{과태료:행정질서 위반에 대한 금전 제재}} 부과 근거를 둡니다.
  - 쉽게 말하면, 규칙을 어기면 비용 부담이 생깁니다.
- 기존 제25조의3은 {{위임·위탁:행정 권한이나 업무 일부를 다른 기관에 맡기는 방식}} 범위를 조정합니다.
  - 쉽게 말하면, 처리할 수 있는 기관이 늘어납니다.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "반복" in str(exc)
    else:
        raise AssertionError("같은 쉬운 풀이 접두어가 반복된 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_allows_eventually_inside_summary_sentence():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
- <mark>결국 이용자 보호를 더 안정적으로 만들려는 법안이에요.</mark>

## 주요 내용
- **운영 기준 정비**: 기준을 더 분명하게 잡아요.

## 무엇이 달라지나
### 1) 인사운용 정비
이 법안은 여러 기준을 따로 보지 않고 한 흐름으로 다시 맞추려는 성격이 강해요. 결국 제도를 더 오래 쓰고, 더 같은 기준으로 운영하겠다는 쪽에 가까워요.
- 숙련 인력을 빨리 교체하기보다 필요한 자리에 오래 두는 쪽으로 무게가 실려요.
- 후속 운영 기준이 중요해요.
""".strip()

    _validate_report_body(report_body)


def test_codex_agent_command_omits_mcp_servers_by_default(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    monkeypatch.delenv("LAW_OC", raising=False)
    monkeypatch.delenv("APIKEY_billsInfo", raising=False)
    monkeypatch.delenv("APIKEY_status", raising=False)

    agent = CodexBillReportAgent(workdir="/tmp/lawdigest-agent", model="gpt-5.3-codex-spark")
    command, stdin_text = agent.build_command(
        prompt="리포트를 작성하세요.",
        output_path=str(tmp_path / "report.md"),
    )

    joined = " ".join(command)
    assert command[:2] == ["codex", "exec"]
    assert "--ignore-user-config" not in command
    assert command.count("--disable") == 3
    assert "plugins" in command
    assert "apps" in command
    assert "memories" in command
    assert "--sandbox" in command
    assert "read-only" in command
    assert "--json" in command
    assert "--output-last-message" in command
    assert stdin_text == "리포트를 작성하세요."
    assert "mcp_servers." not in joined


def test_codex_agent_builds_persistent_initial_and_resume_commands(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)

    agent = CodexBillReportAgent(workdir="/tmp/lawdigest-agent", model="gpt-5.3-codex-spark")
    initial_command, initial_stdin = agent.build_command(
        prompt="첫 번째 리포트를 작성하세요.",
        output_path=str(tmp_path / "first.md"),
        ephemeral=False,
    )
    resume_command, resume_stdin = agent.build_resume_command(
        session_id="thread-batch",
        prompt="두 번째 리포트를 작성하세요.",
        output_path=str(tmp_path / "second.md"),
    )

    assert initial_command[:2] == ["codex", "exec"]
    assert "--ephemeral" not in initial_command
    assert "--output-last-message" in initial_command
    assert initial_stdin == "첫 번째 리포트를 작성하세요."
    assert resume_command[:4] == ["codex", "exec", "resume", "thread-batch"]
    assert "--output-last-message" in resume_command
    assert resume_stdin == "두 번째 리포트를 작성하세요."


def test_codex_agent_uses_dedicated_codex_home(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import (
        CODEX_AUTH_FILES,
        REPORT_SKILL_BODY,
        REPORT_SKILL_NAME,
        CodexBillReportAgent,
    )

    source_home = tmp_path / "source-codex"
    report_home = tmp_path / "report-codex"
    source_home.mkdir()
    for filename in CODEX_AUTH_FILES:
        (source_home / filename).write_text(filename, encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    agent = CodexBillReportAgent(codex_home=str(report_home))
    env = agent.build_environment()

    assert env["CODEX_HOME"] == str(report_home)
    assert not (report_home / "AGENTS.md").exists()
    assert (report_home / "config.toml").exists()
    assert (report_home / "skills" / REPORT_SKILL_NAME / "SKILL.md").read_text(encoding="utf-8") == REPORT_SKILL_BODY
    for filename in CODEX_AUTH_FILES:
        target = report_home / filename
        assert target.is_symlink()
        assert target.resolve() == (source_home / filename).resolve()


def test_codex_agent_disables_external_skills_but_keeps_report_skills(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    home = tmp_path / "home"
    workdir = tmp_path / "repo"
    report_home = tmp_path / "report-codex"
    external_skill = home / ".agents" / "skills" / "external-skill" / "SKILL.md"
    legacy_skill = home / ".codex" / "superpowers" / "skills" / "legacy-skill" / "SKILL.md"
    repo_skill = workdir / ".codex" / "skills" / "repo-skill" / "SKILL.md"
    system_skill = report_home / "skills" / ".system" / "system-skill" / "SKILL.md"
    report_skill = report_home / "skills" / "bill-report-skill" / "SKILL.md"
    future_system_skill = report_home / "skills" / ".system" / "openai-docs" / "SKILL.md"
    for skill in (external_skill, legacy_skill, repo_skill, system_skill, report_skill):
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("---\nname: test\ndescription: test\n---\n", encoding="utf-8")
    (workdir / ".git").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CODEX_HOME", raising=False)

    agent = CodexBillReportAgent(codex_home=str(report_home), workdir=str(workdir))
    agent.build_environment()

    config = (report_home / "config.toml").read_text(encoding="utf-8")
    assert str(external_skill.resolve()) in config
    assert str(legacy_skill.resolve()) in config
    assert str(repo_skill.resolve()) in config
    assert str(system_skill.resolve()) in config
    assert str(future_system_skill.resolve()) in config
    assert str(report_skill.resolve()) not in config
    assert str((report_home / "skills" / "lawdigest-bill-report" / "SKILL.md").resolve()) not in config


def test_codex_agent_passes_dedicated_codex_home_to_subprocess(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    report_home = tmp_path / "report-codex"
    output_path = tmp_path / "report.md"
    report_body = (
        "# 테스트법 일부개정법률안\n\n"
        "## 쉬운 요약\n**본문**이에요. <mark>핵심 변화는 거래 전 정보 확인이에요.</mark>\n\n"
        "## 주요 내용\n- **권한 정비**: 설명이에요.\n\n"
        "## 무엇이 달라지나\n\n"
        "### 1) 허위정보 유포 금지 조문 신설\n\n"
        "제23조의2를 새로 둬 **허위정보 유포**를 금지해요.\n\n"
        "- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.\n"
    )
    seen_env = {}

    def run_codex(*args, **kwargs):
        seen_env.update(kwargs["env"])
        output_path.write_text(report_body, encoding="utf-8")
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

    agent = CodexBillReportAgent(codex_home=str(report_home))
    with patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex):
        result = agent.write_report(
            bill={"bill_id": "PRC_HOME", "bill_name": "테스트법 일부개정법률안"},
            output_path=str(output_path),
        )

    assert result["status"] == "success"
    assert seen_env["CODEX_HOME"] == str(report_home)


def test_codex_agent_command_can_enable_legacy_mcp_servers(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.setenv("LAW_OC", "law-key")
    monkeypatch.setenv("ASSEMBLY_API_KEY", "assembly-key")
    monkeypatch.setenv("KOSIS_API_KEY", "kosis-key")

    agent = CodexBillReportAgent(workdir="/tmp/lawdigest-agent", model="gpt-5.3-codex-spark", enable_mcp=True)
    command, stdin_text = agent.build_command(
        prompt="리포트를 작성하세요.",
        output_path=str(tmp_path / "report.md"),
    )

    joined = " ".join(command)
    assert command[:2] == ["codex", "exec"]
    assert "--ignore-user-config" not in command
    assert command.count("--disable") == 3
    assert "plugins" in command
    assert "apps" in command
    assert "memories" in command
    assert "--sandbox" in command
    assert "read-only" in command
    assert "--json" in command
    assert "--output-last-message" in command
    assert stdin_text == "리포트를 작성하세요."
    assert "mcp_servers.korean-stats.command" in joined
    assert "mcp_servers.korean-law.command" in joined
    assert "mcp_servers.assembly-api.command" in joined
    assert "mcp_servers.open-assembly.command" in joined
    assert "mcp_servers.korean-law.tools.search_law.approval_mode" in joined
    assert "mcp_servers.korean-law.tools.get_legal_term_kb.approval_mode" in joined
    assert "mcp_servers.korean-law.tools.get_legal_to_daily.approval_mode" in joined
    assert "mcp_servers.korean-law.tools.get_daily_to_legal.approval_mode" in joined
    assert "mcp_servers.korean-stats.tools.search_statistics.approval_mode" in joined
    assert "mcp_servers.open-assembly.tools.search_bills.approval_mode" in joined
    assert "mcp_servers.assembly-api.tools.discover_apis.approval_mode" in joined
    assert "korean-law-mcp@latest" in joined
    assert "assembly-api-mcp@latest" in joined
    assert "open-assembly-mcp@latest" in joined


def test_codex_agent_records_operational_usage_metadata(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    output_path = tmp_path / "report.md"
    report_body = (
        "# 테스트법 일부개정법률안\n\n"
        "## 쉬운 요약\n**본문**이에요. <mark>핵심 변화는 거래 전 정보 확인이에요.</mark>\n\n"
        "## 주요 내용\n- **권한 정비**: 설명이에요.\n\n"
        "## 무엇이 달라지나\n\n"
        "### 1) 허위정보 유포 금지 조문 신설\n\n"
        "제23조의2를 새로 둬 **허위정보 유포**를 금지해요.\n\n"
        "- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.\n"
    )
    stdout = "\n".join(
        [
            '{"type":"thread.started","thread_id":"thread-test"}',
            '{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":3,"output_tokens":4,"reasoning_output_tokens":2}}',
        ]
    )

    def run_codex(*args, **kwargs):
        output_path.write_text(report_body, encoding="utf-8")
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=stdout, stderr="")

    agent = CodexBillReportAgent()
    with patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex):
        result = agent.write_report(
            bill={"bill_id": "PRC_TEST", "bill_name": "테스트법 일부개정법률안"},
            output_path=str(output_path),
        )

    assert result["status"] == "success"
    assert result["duration_seconds"] >= 0
    assert result["exit_code"] == 0
    assert result["output_bytes"] == output_path.stat().st_size
    assert result["codex_thread_id"] == "thread-test"
    assert result["token_usage_available"] is True
    assert result["usage"]["input_tokens"] == 10


def test_codex_agent_writes_inspection_artifacts(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    output_path = tmp_path / "report.md"
    inspection_dir = tmp_path / "inspection"
    report_body = (
        "# 테스트법 일부개정법률안\n\n"
        "## 쉬운 요약\n**본문**이에요. <mark>핵심 변화는 거래 전 정보 확인이에요.</mark>\n\n"
        "## 주요 내용\n- **권한 정비**: 설명이에요.\n\n"
        "## 무엇이 달라지나\n\n"
        "### 1) 허위정보 유포 금지 조문 신설\n\n"
        "제23조의2를 새로 둬 **허위정보 유포**를 금지해요.\n\n"
        "- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.\n\n"
        "## 확인한 근거\n- 국회 의안정보시스템 의안 상세\n"
    )
    stdout = "\n".join(
        [
            '{"type":"thread.started","thread_id":"thread-inspect"}',
            '{"type":"item.completed","item":{"type":"function_call","name":"get_bill_detail","call_id":"call_1","arguments":"{\\"bill_id\\":\\"PRC_INSPECT\\"}"}}',
            '{"type":"item.completed","item":{"type":"function_call_output","call_id":"call_1","output":"국회 의안 상세를 확인했습니다."}}',
            '{"type":"turn.completed","usage":{"input_tokens":20,"cached_input_tokens":5,"output_tokens":6,"reasoning_output_tokens":3}}',
        ]
    )

    def run_codex(*args, **kwargs):
        output_path.write_text(report_body, encoding="utf-8")
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=stdout, stderr="")

    agent = CodexBillReportAgent()
    with patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex):
        result = agent.write_report(
            bill={"bill_id": "PRC_INSPECT", "bill_name": "테스트법 일부개정법률안"},
            output_path=str(output_path),
            inspection_dir=str(inspection_dir),
        )

    assert result["inspection_path"].endswith("PRC_INSPECT.inspection.json")
    inspection = json.loads(Path(result["inspection_path"]).read_text(encoding="utf-8"))
    assert inspection["mode"] == "inspection"
    assert inspection["prompt"]["character_count"] > 0
    assert inspection["agent"]["codex_thread_id"] == "thread-inspect"
    assert inspection["agent"]["tool_calls"][0]["name"] == "get_bill_detail"
    assert inspection["evidence"]["reported_sources"] == ["국회 의안정보시스템 의안 상세"]
    assert inspection["validation"]["status"] == "passed"
    event_lines = Path(result["inspection_events_path"]).read_text(encoding="utf-8").splitlines()
    assert len(event_lines) == 4
    assert "국회 의안 상세" in event_lines[2]


def test_codex_agent_uses_gpt_54_mini_by_default():
    from lawdigest_ai.processor.agentic_bill_report import DEFAULT_CODEX_MODEL

    assert DEFAULT_CODEX_MODEL == "gpt-5.4-mini"


def test_codex_agent_requires_assembly_api_key(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    monkeypatch.delenv("APIKEY_billsInfo", raising=False)
    monkeypatch.delenv("APIKEY_status", raising=False)

    agent = CodexBillReportAgent(enable_mcp=True)
    try:
        agent.build_command(prompt="리포트를 작성하세요.", output_path=str(tmp_path / "report.md"))
    except RuntimeError as exc:
        assert "ASSEMBLY_API_KEY" in str(exc)
    else:
        raise AssertionError("ASSEMBLY_API_KEY 없이 Codex MCP 명령이 생성되면 안 됩니다.")


def test_codex_agent_accepts_existing_bills_info_key(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    monkeypatch.setenv("APIKEY_billsInfo", "assembly-key")

    agent = CodexBillReportAgent(enable_mcp=True)
    command, _ = agent.build_command(
        prompt="리포트를 작성하세요.",
        output_path=str(tmp_path / "report.md"),
    )

    assert "mcp_servers.open-assembly.env" in " ".join(command)


def test_run_agentic_bill_reports_writes_markdown_artifacts(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)

    target = {
        "bill_id": "PRC_TEST",
        "bill_number": "2206772",
        "bill_name": "테스트법 일부개정법률안",
        "summary": "테스트 요약",
        "bill_result": "수정가결",
        "stage": "본회의 의결",
        "propose_date": "2026-05-01",
        "proposers": "홍길동의원",
        "committee": "정무위원회",
    }

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=[target],
    ) as fetch_targets, patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout=(
                "# 테스트법 일부개정법률안\n\n"
                "## 쉬운 요약\n**본문**이에요. <mark>핵심 변화는 거래 전 정보 확인이에요.</mark>\n\n"
                "## 주요 내용\n- **권한 정비**: 설명이에요.\n\n"
                "## 무엇이 달라지나\n\n"
                "### 1) 허위정보 유포 금지 조문 신설\n\n"
                "제23조의2를 새로 둬 **허위정보 유포**를 금지해요.\n\n"
                "- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.\n"
            ),
            stderr="",
        )
        result = run_agentic_bill_reports(
            mode="dry_run",
            limit=1,
            output_dir=str(tmp_path),
            )

    assert result["stats"]["target_count"] == 1
    assert result["target"] == "passed_bills"
    assert result["stats"]["success_count"] == 1
    assert result["items"][0]["status"] == "success"
    report_path = Path(result["items"][0]["report_path"])
    assert report_path.exists()
    assert "쉬운 요약" in report_path.read_text(encoding="utf-8")
    fetch_targets.assert_called_once_with(mode="dry_run", limit=1, read_mode=None, target="passed")


def test_run_agentic_bill_reports_can_target_all_bills(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)

    target = {
        "bill_id": "PRC_TEST_ALL",
        "bill_number": "2209999",
        "bill_name": "전체대상 테스트법 일부개정법률안",
        "summary": "테스트 요약",
        "bill_result": "소관위심사",
        "stage": "위원회 심사",
        "propose_date": "2026-05-01",
        "proposers": "홍길동의원",
        "committee": "정무위원회",
    }

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=[target],
    ) as fetch_targets, patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout=(
                "# 전체대상 테스트법 일부개정법률안\n\n"
                "## 쉬운 요약\n**본문**이에요. <mark>핵심 변화는 거래 전 정보 확인이에요.</mark>\n\n"
                "## 주요 내용\n- **권한 정비**: 설명이에요.\n\n"
                "## 무엇이 달라지나\n\n"
                "### 1) 허위정보 유포 금지 조문 신설\n\n"
                "제23조의2를 새로 둬 **허위정보 유포**를 금지해요.\n\n"
                "- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.\n"
            ),
            stderr="",
        )
        result = run_agentic_bill_reports(
            mode="dry_run",
            limit=1,
            output_dir=str(tmp_path),
            target="all",
        )

    assert result["target"] == "all_bills"
    assert result["stats"]["success_count"] == 1
    fetch_targets.assert_called_once_with(mode="dry_run", limit=1, read_mode=None, target="all")


def test_run_agentic_bill_reports_records_usage_meter_snapshot(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)

    target = {
        "bill_id": "PRC_USAGE",
        "bill_number": "2209998",
        "bill_name": "사용량 계측 테스트법 일부개정법률안",
        "summary": "테스트 요약",
        "bill_result": "소관위심사",
        "stage": "위원회 심사",
    }

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=[target],
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout=(
                "# 사용량 계측 테스트법 일부개정법률안\n\n"
                "## 쉬운 요약\n**본문**이에요. <mark>핵심 변화는 거래 전 정보 확인이에요.</mark>\n\n"
                "## 주요 내용\n- **권한 정비**: 설명이에요.\n\n"
                "## 무엇이 달라지나\n\n"
                "### 1) 허위정보 유포 금지 조문 신설\n\n"
                "제23조의2를 새로 둬 **허위정보 유포**를 금지해요.\n\n"
                "- 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.\n"
            ),
            stderr="",
        )
        result = run_agentic_bill_reports(
            mode="dry_run",
            limit=1,
            output_dir=str(tmp_path),
            usage_meter={
                "weekly": {"before_percent": 41.2, "after_percent": 40.7},
                "five_hour": {"before_percent": 8.0, "after_percent": 9.5},
            },
        )

    assert result["usage_meter"] == {
        "weekly": {"before_percent": 41.2, "after_percent": 40.7, "delta_percent": -0.5},
        "five_hour": {"before_percent": 8.0, "after_percent": 9.5, "delta_percent": 1.5},
    }
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["usage_meter"]["weekly"]["delta_percent"] == -0.5


def test_run_agentic_bill_reports_applies_tooltips_from_single_structured_output(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    monkeypatch.delenv("LAW_OC", raising=False)
    monkeypatch.setattr("lawdigest_ai.processor.legal_term_glossary._lookup_local_dictionary_terms", lambda terms: [])
    targets = [
        {
            "bill_id": "PRC_TOOLTIP_TURN",
            "bill_number": "2210999",
            "bill_name": "청문 절차 정비법안",
            "summary": "청문 절차를 더 분명하게 정비합니다.",
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        }
    ]
    report_body = (
        "# 청문 절차 정비법안\n\n"
        "## 쉬운 요약\n**청문 절차**가 더 분명해져요. <mark>핵심 변화는 의견을 말할 기회를 더 분명히 하는 점이에요.</mark>\n\n"
        "## 주요 내용\n- **절차 정비**: 청문 절차를 정비해요.\n\n"
        "## 무엇이 달라지나\n\n"
        "### 1) 의견 확인 절차 정비\n\n"
        "처분 전에 청문 절차를 거치도록 해요.\n\n"
        "- 사용자 입장에서는, 의견을 말할 기회를 더 알기 쉬워져요.\n"
    )

    def run_codex(command, **kwargs):
        output_path = Path(command[command.index("--output-last-message") + 1])
        assert command[:3] != ["codex", "exec", "resume"]
        output_path.write_text(
            json.dumps(
                {
                    "title": "청문 절차 명확화를 위한 청문 절차 정비법안",
                    "report_body": report_body,
                    "tooltips": [
                        {
                            "term": "청문",
                            "surface": "청문 절차",
                            "definition": "이 정의는 후보 정의로 대체돼야 해요.",
                            "reason": "법안의 핵심 절차 용어예요.",
                            "confidence": "high",
                        }
                    ],
                    "rejected": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        usage = {"input_tokens": 100, "cached_input_tokens": 10, "output_tokens": 20, "reasoning_output_tokens": 5}
        stdout = "\n".join([
            '{"type":"thread.started","thread_id":"thread-tooltip"}',
            json.dumps({"type": "turn.completed", "usage": usage}),
        ])
        return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=targets,
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex) as mock_run:
        result = run_agentic_bill_reports(
            mode="dry_run",
            limit=1,
            output_dir=str(tmp_path),
            target="pending",
            report_mode="deep_report",
        )

    assert mock_run.call_count == 1
    assert mock_run.call_args_list[0].args[0][:2] == ["codex", "exec"]
    assert "--ephemeral" not in mock_run.call_args_list[0].args[0]
    assert result["items"][0]["tooltip"]["status"] == "passed"
    assert result["items"][0]["tooltip"]["applied_count"] == 1
    assert result["stats"]["usage_totals"]["input_tokens"] == 100
    assert result["stats"]["usage_totals"]["output_tokens"] == 20
    assert result["stats"]["token_usage_available_count"] == 1
    rendered = Path(result["items"][0]["report_path"]).read_text(encoding="utf-8")
    assert rendered.startswith("# 청문 절차 정비법안")
    assert not rendered.lstrip().startswith("{")
    assert "{{청문 절차:처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차에요.}}" in rendered
    assert "이 정의는 후보 정의" not in rendered


def test_run_agentic_bill_reports_batches_multiple_bills_in_one_session(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    targets = [
        {
            "bill_id": "PRC_BATCH_1",
            "bill_number": "2210001",
            "bill_name": "배치 테스트법안 1",
            "summary": "첫 번째 요약",
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        },
        {
            "bill_id": "PRC_BATCH_2",
            "bill_number": "2210002",
            "bill_name": "배치 테스트법안 2",
            "summary": "두 번째 요약",
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        },
    ]
    report_body_1 = (
        "# 배치 테스트법안 1\n\n"
        "## 쉬운 요약\n**첫 번째** 변화예요. <mark>첫 번째 법안만의 변화가 핵심이에요.</mark>\n\n"
        "## 주요 내용\n- **권한 정비**: 설명이에요.\n\n"
        "## 무엇이 달라지나\n\n"
        "### 1) 첫 번째 제도 정비\n\n"
        "첫 번째 법안 근거만 사용해 제도를 정비해요.\n\n"
        "- 첫 번째 법안의 사용자 영향을 설명해요.\n"
    )
    report_body_2 = (
        "# 배치 테스트법안 2\n\n"
        "## 쉬운 요약\n**두 번째** 변화예요. <mark>두 번째 법안만의 변화가 핵심이에요.</mark>\n\n"
        "## 주요 내용\n- **지원 근거**: 설명이에요.\n\n"
        "## 무엇이 달라지나\n\n"
        "### 1) 두 번째 지원 근거 신설\n\n"
        "두 번째 법안 근거만 사용해 지원 근거를 만들어요.\n\n"
        "- 두 번째 법안의 사용자 영향을 설명해요.\n"
    )

    def run_codex(command, **kwargs):
        output_path = Path(command[command.index("--output-last-message") + 1])
        is_resume = command[:3] == ["codex", "exec", "resume"]
        output_path.write_text(report_body_2 if is_resume else report_body_1, encoding="utf-8")
        usage = {"input_tokens": 202, "cached_input_tokens": 17, "output_tokens": 19, "reasoning_output_tokens": 3}
        if not is_resume:
            usage = {"input_tokens": 101, "cached_input_tokens": 7, "output_tokens": 9, "reasoning_output_tokens": 2}
        stdout = "\n".join([
            '{"type":"thread.started","thread_id":"thread-batch"}',
            json.dumps({"type": "turn.completed", "usage": usage}),
        ])
        return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=targets,
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex) as mock_run:
        result = run_agentic_bill_reports(
            mode="dry_run",
            limit=2,
            output_dir=str(tmp_path),
            target="pending",
            report_mode="deep_report",
            batch_session_size=2,
        )

    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0].args[0][:2] == ["codex", "exec"]
    assert "--ephemeral" not in mock_run.call_args_list[0].args[0]
    assert mock_run.call_args_list[1].args[0][:4] == ["codex", "exec", "resume", "thread-batch"]
    assert result["batch_session_size"] == 2
    assert result["batch_session_count"] == 1
    assert result["stats"]["success_count"] == 2
    assert result["stats"]["usage_totals"]["input_tokens"] == 303
    assert result["stats"]["token_usage_available_count"] == 2
    assert result["sessions"][0]["turn_count"] == 2
    assert result["sessions"][0]["codex_thread_id"] == "thread-batch"
    assert [item["batch_index"] for item in result["items"]] == [1, 1]
    assert [item["batch_turn_index"] for item in result["items"]] == [1, 2]
    assert [item["report_mode"] for item in result["items"]] == ["deep_report", "deep_report"]
    assert all(item["usage_shared"] is False for item in result["items"])
    assert "첫 번째 법안만의 변화" in Path(result["items"][0]["report_path"]).read_text(encoding="utf-8")
    assert "두 번째 법안만의 변화" in Path(result["items"][1]["report_path"]).read_text(encoding="utf-8")


def test_run_agentic_bill_reports_upserts_partial_batch_successes(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    targets = [
        {
            "bill_id": "PRC_PARTIAL_1",
            "bill_number": "2211001",
            "bill_name": "부분 성공 테스트법안 1",
            "summary": "첫 번째 요약",
            "title": "기존 첫 번째 제목",
            "summary_tags": '["기존"]',
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        },
        {
            "bill_id": "PRC_PARTIAL_2",
            "bill_number": "2211002",
            "bill_name": "부분 성공 테스트법안 2",
            "summary": "두 번째 요약",
            "title": "기존 두 번째 제목",
            "summary_tags": '["기존"]',
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        },
    ]
    report_body = (
        "# 부분 성공 테스트법안 1\n\n"
        "## 쉬운 요약\n- 첫 번째 법안은 성공 반영돼야 해요.\n\n"
        "## 주요 내용\n- **지원 근거**: 설명이에요.\n"
        "\n## 무엇이 달라지나\n\n"
        "### 1) 지원 근거 신설\n\n"
        "첫 번째 법안 근거만 사용해 지원 근거를 만들어요.\n"
    )
    upserted_bill_ids: list[str] = []

    def run_codex(command, **kwargs):
        output_path = Path(command[command.index("--output-last-message") + 1])
        if command[:3] != ["codex", "exec", "resume"]:
            output_path.write_text(report_body, encoding="utf-8")
            stdout = '{"type":"thread.started","thread_id":"thread-partial"}'
        else:
            assert upserted_bill_ids == ["PRC_PARTIAL_1"]
            stdout = ""
        return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

    def update_summary(**kwargs):
        upserted_bill_ids.append(kwargs["bill_id"])

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=targets,
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex), patch(
        "lawdigest_ai.processor.agentic_bill_report.update_bill_summary"
    ) as mock_update:
        mock_update.side_effect = update_summary
        result = run_agentic_bill_reports(
            mode="test",
            limit=2,
            output_dir=str(tmp_path),
            target="pending",
            report_mode="deep_report",
            batch_session_size=2,
            failure_retry_attempts=0,
        )

    assert result["stats"]["success_count"] == 1
    assert result["stats"]["failure_count"] == 1
    assert result["stats"]["db_upserted_count"] == 1
    assert result["items"][0]["status"] == "success"
    assert result["items"][1]["status"] == "failed"
    assert "Codex agent report body is empty" in result["items"][1]["error"]
    assert result["items"][1]["failure_type"] == "empty_output"
    mock_update.assert_called_once()
    assert mock_update.call_args.kwargs["bill_id"] == "PRC_PARTIAL_1"


def test_run_agentic_bill_reports_retries_retryable_batch_failures(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    targets = [
        {
            "bill_id": f"PRC_RETRY_{index}",
            "bill_number": f"221110{index}",
            "bill_name": f"재시도 테스트법안 {index}",
            "summary": f"{index}번째 요약",
            "title": f"기존 {index}번째 제목",
            "summary_tags": '["기존"]',
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        }
        for index in (1, 2)
    ]

    def report_output(index: int) -> str:
        bill_name = f"재시도 테스트법안 {index}"
        report_body = (
            f"# {bill_name}\n\n"
            f"## 쉬운 요약\n- <mark>**{index}번째** 리포트예요.</mark>\n\n"
            "## 주요 내용\n- **지원 근거**: 설명이에요.\n\n"
            "## 무엇이 달라지나\n\n"
            "### 1) 지원 근거 신설\n\n"
            f"{index}번째 근거만 사용해 지원 근거를 만들어요.\n"
        )
        return json.dumps(
            {
                "title": f"지원 근거 신설을 위한 {bill_name}",
                "report_body": report_body,
                "tooltips": [],
                "rejected": [],
            },
            ensure_ascii=False,
        )

    calls: list[list[str]] = []

    def run_codex(command, **kwargs):
        calls.append(command)
        output_path = Path(command[command.index("--output-last-message") + 1])
        is_resume = command[:3] == ["codex", "exec", "resume"]
        if not is_resume and len(calls) == 1:
            output_path.write_text(report_output(1), encoding="utf-8")
            stdout = '{"type":"thread.started","thread_id":"thread-retry"}'
        elif is_resume:
            stdout = '{"type":"turn.completed","usage":{"input_tokens":20}}'
        else:
            output_path.write_text(report_output(2), encoding="utf-8")
            stdout = '{"type":"thread.started","thread_id":"thread-retry-single"}'
        return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

    upserted_bill_ids: list[str] = []

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=targets,
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex), patch(
        "lawdigest_ai.processor.agentic_bill_report.update_bill_summary",
        side_effect=lambda **kwargs: upserted_bill_ids.append(kwargs["bill_id"]),
    ):
        result = run_agentic_bill_reports(
            mode="test",
            limit=2,
            output_dir=str(tmp_path),
            target="pending",
            report_mode="deep_report",
            batch_session_size=2,
            failure_retry_attempts=1,
        )

    assert len(calls) == 3
    assert calls[1][:3] == ["codex", "exec", "resume"]
    assert calls[2][:3] != ["codex", "exec", "resume"]
    assert result["stats"]["success_count"] == 2
    assert result["stats"]["failure_count"] == 0
    assert result["stats"]["retried_item_count"] == 1
    assert result["stats"]["retry_success_count"] == 1
    assert result["items"][1]["retry"]["attempt_count"] == 1
    assert result["items"][1]["retry"]["history"][0]["attempt"] == 0
    assert result["items"][1]["retry"]["history"][0]["failure_type"] == "empty_output"
    assert result["stats"]["usage_totals"]["input_tokens"] == 20
    assert upserted_bill_ids == ["PRC_RETRY_1", "PRC_RETRY_2"]


def test_run_agentic_bill_reports_preserves_success_before_later_batch_configuration_error(tmp_path):
    from lawdigest_ai.processor.agentic_bill_report import build_bill_report_evidence, run_agentic_bill_reports

    targets = [
        {"bill_id": "PRC_CONFIG_BATCH_1", "bill_name": "배치 설정 테스트법안 1", "summary": "첫 번째 요약"},
        {"bill_id": "PRC_CONFIG_BATCH_2", "bill_name": "배치 설정 테스트법안 2", "summary": "두 번째 요약"},
    ]
    evidence_calls = 0

    def build_evidence(bill, *, report_mode):
        nonlocal evidence_calls
        evidence_calls += 1
        if evidence_calls == 2:
            raise RuntimeError("evidence config failed")
        return build_bill_report_evidence(bill, report_mode=report_mode)

    def run_codex(command, **kwargs):
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text(
            "# 배치 설정 테스트법안 1\n\n"
            "## 쉬운 요약\n- **첫 항목**은 성공해요. <mark>뒤 항목 오류가 앞 결과를 지우면 안 돼요.</mark>\n\n"
            "## 주요 내용\n- **처리 보존**: 성공 결과를 유지해요.\n\n"
            "## 무엇이 달라지나\n\n### 1) 처리 결과 보존\n\n첫 항목 결과를 그대로 유지해요.\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout='{"type":"thread.started","thread_id":"thread-config"}',
            stderr="",
        )

    with patch("lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets", return_value=targets), patch(
        "lawdigest_ai.processor.agentic_bill_report.build_bill_report_evidence", side_effect=build_evidence
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex) as run_process:
        result = run_agentic_bill_reports(limit=2, output_dir=str(tmp_path), batch_session_size=2)

    assert run_process.call_count == 1
    assert result["items"][0]["status"] == "success"
    assert result["items"][1]["status"] == "failed"
    assert result["items"][1]["failure_type"] == "configuration_error"
    assert result["stats"]["success_count"] == 1
    assert result["stats"]["retried_item_count"] == 0


def test_run_agentic_bill_reports_can_disable_failure_retries(tmp_path):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent, run_agentic_bill_reports

    targets = [{"bill_id": "PRC_NO_RETRY_1", "bill_name": "재시도 비활성화법안 1"}, {"bill_id": "PRC_NO_RETRY_2", "bill_name": "재시도 비활성화법안 2"}]
    batch_result = {
        "items": [
            {"bill_id": bill["bill_id"], "bill_name": bill["bill_name"], "status": "failed", "failure_type": "empty_output", "error": "empty", "batch_index": 1}
            for bill in targets
        ],
        "session": {"batch_index": 1, "token_usage_available": False},
    }

    with patch("lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets", return_value=targets), patch.object(
        CodexBillReportAgent, "write_reports_batch", return_value=batch_result
    ), patch.object(CodexBillReportAgent, "write_report") as write_report:
        result = run_agentic_bill_reports(limit=2, output_dir=str(tmp_path), batch_session_size=2, failure_retry_attempts=0)

    write_report.assert_not_called()
    assert result["stats"]["retried_item_count"] == 0
    assert result["stats"]["failure_count"] == 2


@pytest.mark.parametrize("retry_attempts", [-1, 1.5])
def test_run_agentic_bill_reports_rejects_invalid_failure_retry_attempts(tmp_path, retry_attempts):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    with pytest.raises(ValueError, match="failure_retry_attempts"):
        run_agentic_bill_reports(output_dir=str(tmp_path), failure_retry_attempts=retry_attempts)


def test_codex_agent_classifies_zero_byte_output_as_empty_output(tmp_path):
    from lawdigest_ai.processor.agentic_bill_report import BillReportGenerationError, CodexBillReportAgent

    output_path = tmp_path / "empty.md"
    output_path.touch()
    with patch(
        "lawdigest_ai.processor.agentic_bill_report.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
    ), pytest.raises(BillReportGenerationError) as exc_info:
        CodexBillReportAgent().write_report(
            bill={"bill_id": "PRC_EMPTY", "bill_name": "빈 출력법안"},
            output_path=str(output_path),
        )

    assert exc_info.value.details["failure_type"] == "empty_output"


def test_codex_agent_does_not_reuse_preexisting_report_when_retry_writes_nothing(tmp_path):
    from lawdigest_ai.processor.agentic_bill_report import BillReportGenerationError, CodexBillReportAgent

    output_path = tmp_path / "stale.md"
    output_path.write_text(
        "# 이전 출력법안\n\n## 쉬운 요약\n- **이전 결과**예요. <mark>재사용하면 안 돼요.</mark>\n\n## 주요 내용\n- **기존 결과**: 설명이에요.\n",
        encoding="utf-8",
    )
    with patch(
        "lawdigest_ai.processor.agentic_bill_report.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='{"type":"turn.completed"}', stderr=""),
    ), pytest.raises(BillReportGenerationError) as exc_info:
        CodexBillReportAgent().write_report(
            bill={"bill_id": "PRC_STALE", "bill_name": "이전 출력법안"},
            output_path=str(output_path),
        )

    assert exc_info.value.details["failure_type"] == "empty_output"


def test_codex_agent_classifies_environment_preparation_failure_as_configuration_error(tmp_path):
    from lawdigest_ai.processor.agentic_bill_report import BillReportGenerationError, CodexBillReportAgent

    with patch.object(CodexBillReportAgent, "build_environment", side_effect=OSError("config unavailable")), patch(
        "lawdigest_ai.processor.agentic_bill_report.subprocess.run"
    ) as run_process, pytest.raises(BillReportGenerationError) as exc_info:
        CodexBillReportAgent().write_report(
            bill={"bill_id": "PRC_CONFIG", "bill_name": "설정 오류법안"},
            output_path=str(tmp_path / "config.md"),
        )

    run_process.assert_not_called()
    assert exc_info.value.details["failure_type"] == "configuration_error"


def test_run_agentic_bill_reports_retries_until_exhausted_before_stop_on_error(tmp_path):
    from lawdigest_ai.processor.agentic_bill_report import BillReportGenerationError, CodexBillReportAgent, run_agentic_bill_reports

    targets = [{"bill_id": "PRC_STOP_1", "bill_name": "재시도 소진법안 1"}, {"bill_id": "PRC_STOP_2", "bill_name": "재시도 소진법안 2"}]
    batch_result = {
        "items": [
            {"bill_id": bill["bill_id"], "bill_name": bill["bill_name"], "status": "failed", "failure_type": "empty_output", "error": "empty", "batch_index": 1}
            for bill in targets
        ],
        "session": {"batch_index": 1, "token_usage_available": False},
    }

    retry_calls: list[str] = []

    def fail_retry(self, *, bill, output_path, **kwargs):
        retry_calls.append(bill["bill_id"])
        raise BillReportGenerationError(
            "still invalid",
            details={"bill_id": bill["bill_id"], "report_path": output_path, "failure_type": "invalid_output", "usage": {"input_tokens": 3}},
        )

    with patch("lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets", return_value=targets), patch.object(
        CodexBillReportAgent, "write_reports_batch", return_value=batch_result
    ), patch.object(CodexBillReportAgent, "write_report", fail_retry), pytest.raises(
        BillReportGenerationError, match="still invalid"
    ):
        run_agentic_bill_reports(
            limit=2,
            output_dir=str(tmp_path),
            batch_session_size=2,
            failure_retry_attempts=2,
            stop_on_error=True,
        )

    assert len(retry_calls) == 4
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["stats"]["usage_totals"]["input_tokens"] == 12
    assert [item["retry"]["attempt_count"] for item in manifest["items"]] == [2, 2]


def test_run_agentic_bill_reports_stops_retrying_after_retry_persistence_failure(tmp_path):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent, run_agentic_bill_reports

    targets = [{"bill_id": "PRC_RETRY_DB_1", "bill_name": "재시도 저장 실패법안 1"}, {"bill_id": "PRC_RETRY_DB_2", "bill_name": "재시도 저장 실패법안 2"}]
    batch_result = {
        "items": [
            {"bill_id": bill["bill_id"], "bill_name": bill["bill_name"], "status": "failed", "failure_type": "empty_output", "error": "empty", "batch_index": 1}
            for bill in targets
        ],
        "session": {"batch_index": 1, "token_usage_available": False},
    }

    retry_calls: list[str] = []

    def successful_retry(self, *, bill, output_path, **kwargs):
        retry_calls.append(bill["bill_id"])
        return {"bill_id": bill["bill_id"], "bill_name": bill["bill_name"], "status": "success", "report_path": output_path, "title": f"변화를 위한 {bill['bill_name']}", "usage": {"input_tokens": 7}}

    with patch("lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets", return_value=targets), patch.object(
        CodexBillReportAgent, "write_reports_batch", return_value=batch_result
    ), patch.object(CodexBillReportAgent, "write_report", successful_retry), patch(
        "lawdigest_ai.processor.agentic_bill_report._persist_successful_report_item", side_effect=RuntimeError("db down")
    ):
        result = run_agentic_bill_reports(mode="test", limit=2, output_dir=str(tmp_path), batch_session_size=2, failure_retry_attempts=3)

    assert len(retry_calls) == 2
    assert result["stats"]["retry_success_count"] == 0
    assert result["stats"]["usage_totals"]["input_tokens"] == 14
    assert all(item["failure_type"] == "persistence_error" for item in result["items"])
    assert all(item["retry"]["attempt_count"] == 1 for item in result["items"])


def test_run_agentic_bill_reports_does_not_retry_persistence_failures(tmp_path):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent, run_agentic_bill_reports

    targets = [{"bill_id": "PRC_DB_1", "bill_name": "저장 실패법안 1"}, {"bill_id": "PRC_DB_2", "bill_name": "저장 실패법안 2"}]

    def write_batch(self, *, bills, success_callback, **kwargs):
        items = []
        for bill in bills:
            item = {"bill_id": bill["bill_id"], "bill_name": bill["bill_name"], "status": "success", "title": f"변화를 위한 {bill['bill_name']}", "report_path": str(tmp_path / f"{bill['bill_id']}.md"), "batch_index": 1}
            try:
                item["db_upserted"] = success_callback(bill, item)
            except Exception as exc:
                item = {**item, "status": "failed", "failure_type": "persistence_error", "error": str(exc)}
            items.append(item)
        return {"items": items, "session": {"batch_index": 1, "token_usage_available": False}}

    with patch("lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets", return_value=targets), patch.object(
        CodexBillReportAgent, "write_reports_batch", write_batch
    ), patch("lawdigest_ai.processor.agentic_bill_report._persist_successful_report_item", side_effect=RuntimeError("db down")), patch.object(
        CodexBillReportAgent, "write_report"
    ) as write_report:
        result = run_agentic_bill_reports(mode="test", limit=2, output_dir=str(tmp_path), batch_session_size=2)

    write_report.assert_not_called()
    assert result["stats"]["retried_item_count"] == 0
    assert [item["failure_type"] for item in result["items"]] == ["persistence_error", "persistence_error"]


def test_run_agentic_bill_reports_maps_report_bodies_without_agent_bill_id(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    targets = [
        {
            "bill_id": "PRC_REPAIR_1",
            "bill_number": "2212001",
            "bill_name": "식별자 복구 테스트법안 1",
            "summary": "첫 번째 요약",
            "title": "기존 첫 번째 제목",
            "summary_tags": '["기존"]',
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        },
        {
            "bill_id": "PRC_REPAIR_2",
            "bill_number": "2212002",
            "bill_name": "식별자 복구 테스트법안 2",
            "summary": "두 번째 요약",
            "title": "기존 두 번째 제목",
            "summary_tags": '["기존"]',
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        },
    ]
    report_body_1 = (
        "# 식별자 복구 테스트법안 1\n\n"
        "## 쉬운 요약\n- 첫 번째 법안은 원래 식별자로 저장돼야 해요.\n\n"
        "## 주요 내용\n- **지원 근거**: 첫 번째 설명이에요.\n"
        "\n## 무엇이 달라지나\n\n"
        "### 1) 지원 근거 신설\n\n"
        "첫 번째 법안 근거만 사용해 지원 근거를 만들어요.\n"
    )
    report_body_2 = (
        "# 식별자 복구 테스트법안 2\n\n"
        "## 쉬운 요약\n- 두 번째 법안은 제목으로 식별자를 복구해야 해요.\n\n"
        "## 주요 내용\n- **관리 절차**: 두 번째 설명이에요.\n"
        "\n## 무엇이 달라지나\n\n"
        "### 1) 관리 절차 정비\n\n"
        "두 번째 법안 근거만 사용해 관리 절차를 정비해요.\n"
    )

    def run_codex(command, **kwargs):
        output_path = Path(command[command.index("--output-last-message") + 1])
        if command[:3] == ["codex", "exec", "resume"]:
            output_path.write_text(report_body_2, encoding="utf-8")
            stdout = '{"type":"thread.started","thread_id":"thread-repair"}'
        else:
            output_path.write_text(report_body_1, encoding="utf-8")
            stdout = '{"type":"thread.started","thread_id":"thread-repair"}'
        return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=targets,
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex), patch(
        "lawdigest_ai.processor.agentic_bill_report.update_bill_summary"
    ) as mock_update:
        result = run_agentic_bill_reports(
            mode="test",
            limit=2,
            output_dir=str(tmp_path),
            target="pending",
            report_mode="deep_report",
            batch_session_size=2,
        )

    assert result["stats"]["success_count"] == 2
    assert result["stats"]["failure_count"] == 0
    assert result["stats"]["db_upserted_count"] == 2
    assert [item["status"] for item in result["items"]] == ["success", "success"]
    assert [call.kwargs["bill_id"] for call in mock_update.call_args_list] == ["PRC_REPAIR_1", "PRC_REPAIR_2"]
    assert "두 번째 법안은 제목으로 식별자를 복구해야 해요" in Path(
        result["items"][1]["report_path"]
    ).read_text(encoding="utf-8")


def test_run_agentic_bill_reports_unwraps_single_report_json_in_batch_turn(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    targets = [
        {
            "bill_id": "PRC_JSON_BATCH_1",
            "bill_number": "2213001",
            "bill_name": "JSON 복구 테스트법안 1",
            "summary": "첫 번째 요약",
            "title": "기존 첫 번째 제목",
            "summary_tags": '["기존"]',
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        },
        {
            "bill_id": "PRC_JSON_BATCH_2",
            "bill_number": "2213002",
            "bill_name": "JSON 복구 테스트법안 2",
            "summary": "두 번째 요약",
            "title": "기존 두 번째 제목",
            "summary_tags": '["기존"]',
            "bill_result": "소관위심사",
            "stage": "위원회 심사",
        },
    ]

    def report_body(title: str, summary: str) -> str:
        return (
            f"# {title}\n\n"
            f"## 쉬운 요약\n- {summary} 리포트가 Markdown으로 저장돼야 해요.\n\n"
            "## 주요 내용\n- **지원 근거**: 설명이에요.\n"
            "\n## 무엇이 달라지나\n\n"
            "### 1) 지원 근거 신설\n\n"
            f"{summary} 근거만 사용해 지원 근거를 만들어요.\n"
        )

    def run_codex(command, **kwargs):
        output_path = Path(command[command.index("--output-last-message") + 1])
        is_resume = command[:3] == ["codex", "exec", "resume"]
        body = report_body(
            "JSON 복구 테스트법안 2" if is_resume else "JSON 복구 테스트법안 1",
            "두 번째 법안" if is_resume else "첫 번째 법안",
        )
        bill_name = "JSON 복구 테스트법안 2" if is_resume else "JSON 복구 테스트법안 1"
        output_path.write_text(
            json.dumps(
                {
                    "reports": [
                        {
                            "title": f"지원 근거 신설을 위한 {bill_name}",
                            "report_body": body,
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        stdout = '{"type":"thread.started","thread_id":"thread-json-repair"}'
        return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=targets,
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex), patch(
        "lawdigest_ai.processor.agentic_bill_report.update_bill_summary"
    ) as mock_update:
        result = run_agentic_bill_reports(
            mode="test",
            limit=2,
            output_dir=str(tmp_path),
            target="pending",
            report_mode="deep_report",
            batch_session_size=2,
        )

    assert result["stats"]["success_count"] == 2
    assert result["stats"]["failure_count"] == 0
    assert [call.kwargs["bill_id"] for call in mock_update.call_args_list] == ["PRC_JSON_BATCH_1", "PRC_JSON_BATCH_2"]
    assert [call.kwargs["title"] for call in mock_update.call_args_list] == [
        "지원 근거 신설을 위한 JSON 복구 테스트법안 1",
        "지원 근거 신설을 위한 JSON 복구 테스트법안 2",
    ]
    for item in result["items"]:
        body = Path(item["report_path"]).read_text(encoding="utf-8")
        assert body.startswith("# JSON 복구 테스트법안")
        assert not body.lstrip().startswith("{")


def test_batch_report_parser_ignores_agent_bill_id_when_title_matches():
    from lawdigest_ai.processor.agentic_bill_report import _parse_batch_report_output

    report_body_1 = "# 파이프라인 기준 테스트법안 1\n\n## 쉬운 요약\n- 첫 번째예요.\n\n## 주요 내용\n- **항목**: 설명이에요.\n"
    report_body_2 = "# 파이프라인 기준 테스트법안 2\n\n## 쉬운 요약\n- 두 번째예요.\n\n## 주요 내용\n- **항목**: 설명이에요.\n"

    parsed = _parse_batch_report_output(
        json.dumps(
            {
                "reports": [
                    {"bill_id": "WRONG_ID_2", "report_body": report_body_1},
                    {"bill_id": "WRONG_ID_1", "report_body": report_body_2},
                ]
            },
            ensure_ascii=False,
        ),
        expected_bill_ids=["PIPELINE_ID_1", "PIPELINE_ID_2"],
        expected_bills=[
            {"bill_id": "PIPELINE_ID_1", "bill_name": "파이프라인 기준 테스트법안 1"},
            {"bill_id": "PIPELINE_ID_2", "bill_name": "파이프라인 기준 테스트법안 2"},
        ],
    )

    assert parsed == {
        "PIPELINE_ID_1": report_body_1,
        "PIPELINE_ID_2": report_body_2,
    }


def test_run_agentic_bill_reports_runs_codex_sessions_in_parallel(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent, run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    targets = [
        {"bill_id": "PRC_PARALLEL_1", "bill_name": "병렬 테스트법 1"},
        {"bill_id": "PRC_PARALLEL_2", "bill_name": "병렬 테스트법 2"},
    ]
    lock = threading.Lock()
    both_started = threading.Event()
    started_count = 0

    def write_report(self, *, bill, output_path, inspection_dir=None, report_mode="auto"):
        nonlocal started_count
        with lock:
            started_count += 1
            if started_count == 2:
                both_started.set()
        if not both_started.wait(timeout=1):
            raise AssertionError("두 리포트 세션이 동시에 시작되지 않았습니다.")
        Path(output_path).write_text("# 병렬 테스트\n", encoding="utf-8")
        return {
            "bill_id": bill["bill_id"],
            "bill_name": bill["bill_name"],
            "report_path": output_path,
            "status": "success",
        }

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=targets,
    ), patch.object(CodexBillReportAgent, "write_report", write_report):
        result = run_agentic_bill_reports(
            mode="dry_run",
            limit=2,
            output_dir=str(tmp_path),
            concurrency=2,
            batch_session_size=1,
        )

    assert result["concurrency"] == 2
    assert result["stats"]["success_count"] == 2
    assert [item["bill_id"] for item in result["items"]] == ["PRC_PARALLEL_1", "PRC_PARALLEL_2"]


def test_run_agentic_bill_reports_runs_batch_sessions_in_parallel(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    targets = [
        {"bill_id": "PRC_BATCH_PARALLEL_1", "bill_name": "배치 병렬 테스트법 1", "summary": "첫 번째 요약"},
        {"bill_id": "PRC_BATCH_PARALLEL_2", "bill_name": "배치 병렬 테스트법 2", "summary": "두 번째 요약"},
        {"bill_id": "PRC_BATCH_PARALLEL_3", "bill_name": "배치 병렬 테스트법 3", "summary": "세 번째 요약"},
        {"bill_id": "PRC_BATCH_PARALLEL_4", "bill_name": "배치 병렬 테스트법 4", "summary": "네 번째 요약"},
    ]
    name_by_id = {target["bill_id"]: target["bill_name"] for target in targets}
    lock = threading.Lock()
    both_batches_started = threading.Event()
    first_turn_count = 0

    def report_body(output_path: Path) -> str:
        title = name_by_id[output_path.stem]
        return (
            f"# {title}\n\n"
            "## 쉬운 요약\n"
            "**병렬 배치**로 각 법안 리포트가 생성돼요. <mark>여러 배치 세션이 동시에 시작되는지가 핵심이에요.</mark>\n\n"
            "## 주요 내용\n- **처리 구조**: 배치 세션은 병렬로 시작되고, 세션 안에서는 순차로 이어져요.\n\n"
            "## 무엇이 달라지나\n\n"
            "### 1) 처리 속도 개선\n\n"
            "여러 배치 세션을 동시에 실행해 전체 처리 시간을 줄여요.\n"
            "\n- 배치 안의 다음 법안은 같은 세션에서 이어서 처리해요.\n"
        )

    def run_codex(command, **kwargs):
        nonlocal first_turn_count
        output_path = Path(command[command.index("--output-last-message") + 1])
        is_resume = command[:3] == ["codex", "exec", "resume"]
        if not is_resume:
            with lock:
                first_turn_count += 1
                thread_id = f"thread-batch-parallel-{first_turn_count}"
                if first_turn_count == 2:
                    both_batches_started.set()
            if not both_batches_started.wait(timeout=5):
                raise AssertionError("두 배치 세션이 동시에 시작되지 않았습니다.")
        else:
            thread_id = command[3]
        output_path.write_text(report_body(output_path), encoding="utf-8")
        stdout = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": thread_id}),
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}),
            ]
        )
        return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=targets,
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run", side_effect=run_codex) as mock_run:
        result = run_agentic_bill_reports(
            mode="dry_run",
            limit=4,
            output_dir=str(tmp_path),
            target="pending",
            report_mode="deep_report",
            concurrency=2,
            batch_session_size=2,
        )

    commands = [call.args[0] for call in mock_run.call_args_list]
    assert result["concurrency"] == 2
    assert result["batch_session_size"] == 2
    assert result["batch_session_count"] == 2
    assert result["stats"]["success_count"] == 4
    assert sum(command[:3] == ["codex", "exec", "resume"] for command in commands) == 2
    assert all(session["turn_count"] == 2 for session in result["sessions"])
    assert [item["batch_index"] for item in result["items"]] == [1, 1, 2, 2]


def test_agentic_report_validates_generated_card_title_contract():
    from lawdigest_ai.processor.agentic_bill_report import _validate_generated_title

    bill = {"bill_name": "선거관리위원회법 일부개정법률안"}
    _validate_generated_title(
        "선관위원장 상임화·상임위원 확대 및 감사·인사검증 강화를 위한 선거관리위원회법 일부개정법률안",
        bill,
        required=True,
    )

    with pytest.raises(RuntimeError, match="제목형 계약"):
        _validate_generated_title(
            "중앙선거관리위원회는 선거사무 전반을 중립적이고 책임 있게 수행하여야 하는 헌법기관임.",
            bill,
            required=True,
        )

    with pytest.raises(RuntimeError, match="title이 없습니다"):
        _validate_generated_title(None, bill, required=True)


def test_agentic_report_replaces_source_sentence_with_generated_card_title():
    from lawdigest_ai.processor.agentic_bill_report import _build_db_summary_payload

    bill = {
        "bill_id": "PRC_DB",
        "bill_name": "선거관리위원회법 일부개정법률안",
        "title": (
            "중앙선거관리위원회는 민주주의의 근간인 선거의 공정성과 투명성을 확보하고, "
            "선거ㆍ투표관리, 조사ㆍ단속, 조직운영 등 선거사무 전반을 중립적이고 책임 있게 "
            "수행하여야 하는 헌법기관임."
        ),
        "summary_tags": '["기존태그"]',
    }
    report_body = """
# 선거관리위원회법 일부개정법률안

## 쉬운 요약
- 중앙선거관리위원회의 내부 관리·감독을 더 촘촘하게 만들기 위한 법률 개정안이에요.
- 위원장을 상임으로 바꾸고 상임위원을 3명으로 늘려요.

## 무엇이 달라지나
### 1) 위원회 운영 방식 변경
위원장을 상임으로 바꾸고 상임위원을 확대해요.

## 확인한 근거
- 국회 의안정보시스템
""".strip()

    generated_title = (
        "선관위원장 상임화·상임위원 확대 및 감사·인사검증 강화를 위한 "
        "선거관리위원회법 일부개정법률안"
    )
    payload = _build_db_summary_payload(
        bill=bill,
        report_body=report_body,
        generated_title=generated_title,
    )

    assert payload["title"] == generated_title
    assert payload["summary_tags"] == '["기존태그"]'
    assert "## 쉬운 요약" in payload["gpt_summary"]
    assert "### 1) 위원회 운영 방식 변경" in payload["gpt_summary"]
    assert "# 선거관리위원회법 일부개정법률안" not in payload["gpt_summary"]
    assert "확인한 근거" not in payload["gpt_summary"]


def test_agentic_report_rebuilds_overlong_title_prefix():
    from lawdigest_ai.processor.agentic_bill_report import _build_db_summary_payload

    bill_name = "인공지능 데이터센터 산업 진흥에 관한 특별법안(대안)"
    bill = {
        "bill_id": "PRC_AI_DC",
        "bill_name": bill_name,
        "title": (
            "인공지능 데이터센터의 신속한 구축과 운영 지원을 위한 행정·재정적 근거를 마련하고 "
            "인허가 절차 간소화 및 각종 특례를 규정하기 위한 "
            "인공지능 데이터센터 산업 진흥에 관한 특별법안(대안)"
        ),
        "summary_tags": None,
    }
    report_body = """
# 인공지능 데이터센터 산업 진흥에 관한 특별법안(대안)

## 쉬운 요약
- 인공지능 데이터센터를 **빨리 짓고 안정적으로 돌리기 위한 특별법**이에요.
- 국가와 지자체가 전력, 용수, 도로, 통신 같은 기반부터 우선 챙기게 해요.

## 주요 내용
### 1) 빠른 구축 지원
<mark>인허가를 묶어 처리할 수 있게 해요.</mark>
""".strip()

    payload = _build_db_summary_payload(bill=bill, report_body=report_body)

    assert payload["title"] == (
        "전력·용수 기반과 인허가 특례로 인공지능 데이터센터 구축·운영 지원을 위한 "
        "인공지능 데이터센터 산업 진흥에 관한 특별법안(대안)"
    )
    assert payload["title"].endswith(bill_name)


def test_agentic_report_rebuilds_title_without_bad_particles():
    from lawdigest_ai.processor.agentic_bill_report import _build_db_summary_payload

    cases = [
        (
            "농지법 일부개정법률안(대안)",
            "농지의 실제 이용 상태를 더 잘 파악하고, 방치된 농지를 정리하게 해요.",
            "농지 이용 실태조사와 유휴농지 관리 강화를 위한 농지법 일부개정법률안(대안)",
        ),
        (
            "해운법 일부개정법률안(대안)",
            "섬 주민이 끊기지 않게 배를 이용할 수 있도록 지원해요.",
            "섬 지역 항로 단절 방지와 여객선 운항 지원 강화를 위한 해운법 일부개정법률안(대안)",
        ),
        (
            "지속가능한 연근해어업 발전법안(대안)",
            "연근해에서 잡고 기르는 어업을 오래 이어갈 수 있게 관리체계를 만들어요.",
            "어업활동 보고와 통합관리시스템 기반 연근해어업 관리체계 구축을 위한 지속가능한 연근해어업 발전법안(대안)",
        ),
    ]

    malformed_titles = {
        "농지법 일부개정법률안(대안)": "농지의 실제 이용 상태를 더 잘 파악하고, 방치된을 위한 농지법 일부개정법률안(대안)",
        "해운법 일부개정법률안(대안)": "섬 주민이 끊기지 않게 배를을 위한 해운법 일부개정법률안(대안)",
        "지속가능한 연근해어업 발전법안(대안)": (
            "불법어업 예방을 위한 어업활동 보고 의무화 및 통합관리시스템 구축을 위한 "
            "지속가능한 연근해어업 발전법안(대안)"
        ),
    }

    for bill_name, first_bullet, expected in cases:
        payload = _build_db_summary_payload(
            bill={
                "bill_id": "PRC_CASE",
                "bill_name": bill_name,
                "title": malformed_titles[bill_name],
                "summary_tags": None,
            },
            report_body=f"## 쉬운 요약\n- {first_bullet}\n\n## 주요 내용\n### 1) 변화\n본문",
        )

        assert payload["title"] == expected
        assert "된을 위한" not in payload["title"]
        assert "를을 위한" not in payload["title"]


def test_run_agentic_bill_reports_upserts_successful_items(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent, run_agentic_bill_reports

    monkeypatch.setenv("ASSEMBLY_API_KEY", "assembly-key")
    target = {
        "bill_id": "PRC_DB_UPSERT",
        "bill_name": "업서트 테스트법 일부개정법률안",
        "title": "기존 제목",
        "summary_tags": '["기존태그"]',
    }
    report_path = tmp_path / "PRC_DB_UPSERT.md"
    report_path.write_text(
        "# 업서트 테스트법 일부개정법률안\n\n"
        "## 쉬운 요약\n- 지원 근거를 분명히 해요.\n\n"
        "## 주요 내용\n- **지원 근거**: 설명이에요.\n",
        encoding="utf-8",
    )

    def write_report(self, *, bill, output_path, inspection_dir=None, report_mode="auto"):
        return {
            "bill_id": bill["bill_id"],
            "bill_name": bill["bill_name"],
            "title": "지원 근거 명확화를 위한 업서트 테스트법 일부개정법률안",
            "report_path": str(report_path),
            "status": "success",
        }

    with patch(
        "lawdigest_ai.processor.agentic_bill_report._fetch_bill_report_targets",
        return_value=[target],
    ), patch.object(CodexBillReportAgent, "write_report", write_report), patch(
        "lawdigest_ai.processor.agentic_bill_report.update_bill_summary"
    ) as mock_update:
        result = run_agentic_bill_reports(
            mode="test",
            limit=1,
            output_dir=str(tmp_path),
            batch_session_size=1,
        )

    assert result["stats"]["db_upserted_count"] == 1
    mock_update.assert_called_once()
    assert mock_update.call_args.kwargs["title"] == (
        "지원 근거 명확화를 위한 업서트 테스트법 일부개정법률안"
    )
    assert "쉬운 요약" in mock_update.call_args.kwargs["gpt_summary"]


def test_fetch_bill_report_targets_uses_null_summary_tags_when_column_absent():
    from lawdigest_ai.processor.agentic_bill_report import _fetch_bill_report_targets

    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = []

    with patch(
        "lawdigest_ai.processor.agentic_bill_report.get_db_connection",
        return_value=conn,
    ), patch(
        "lawdigest_ai.processor.agentic_bill_report.get_bill_table_columns",
        return_value={"bill_id", "title", "summary"},
    ):
        _fetch_bill_report_targets(mode="dry_run", limit=1, read_mode="prod", target="all")

    executed_query = cur.execute.call_args.args[0]
    assert "NULL AS summary_tags" in executed_query
    assert "ORDER BY propose_date DESC, bill_id DESC" in executed_query


def test_fetch_bill_report_targets_can_select_pending_bills():
    from lawdigest_ai.processor.agentic_bill_report import _fetch_bill_report_targets

    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = []

    with patch(
        "lawdigest_ai.processor.agentic_bill_report.get_db_connection",
        return_value=conn,
    ), patch(
        "lawdigest_ai.processor.agentic_bill_report.get_bill_table_columns",
        return_value={"bill_id", "title", "summary", "summary_tags"},
    ):
        _fetch_bill_report_targets(mode="dry_run", limit=1, read_mode="prod", target="pending")

    executed_query = cur.execute.call_args.args[0]
    assert "NOT (COALESCE(bill_result, '') LIKE" in executed_query
    assert "COALESCE(bill_result, '') NOT LIKE" in executed_query
