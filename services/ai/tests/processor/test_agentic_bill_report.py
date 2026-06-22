import json
import subprocess
from pathlib import Path
from unittest.mock import patch


def test_agentic_report_prompt_requires_active_mcp_research():
    from lawdigest_ai.processor.agentic_bill_report import build_bill_report_prompt

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

    assert "Lawdigest가 보유한 법안 후보" in prompt
    assert "실제 처리결과에 맞게 설명" in prompt
    assert "이미 통과된 법안" not in prompt
    assert "MCP 도구를 능동적으로 사용" in prompt
    assert "open-assembly" in prompt
    assert "assembly-api" in prompt
    assert "korean-law" in prompt
    assert "korean-stats" in prompt
    assert "법안의 통과 경로" in prompt
    assert "현행법 및 개정 법령 맥락" in prompt
    assert "통계청 공식 통계" in prompt


def test_agentic_report_prompt_targets_user_facing_report():
    from lawdigest_ai.processor.agentic_bill_report import build_bill_report_prompt

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

    assert "사용자에게 보여줄 최종 법안 리포트" in prompt
    assert "쉬운 요약" in prompt
    assert "쉬운 말로 충분히 설명하는 것" in prompt
    assert "5개 불릿" in prompt
    assert "복합 개정안은 최종 리포트가 8,000자 안팎" in prompt
    assert "**항목 제목**: 쉬운 설명" in prompt
    assert "**부당한 표시·광고 제한**: 허위·과장 등 소비자를 오도할 수 있는 표현을 규제해요." in prompt
    assert "Lawdigest 요약 개선 제안" not in prompt
    assert "사용한 MCP 도구와 출처" not in prompt
    assert "내부 조사 로그" in prompt
    assert "MCP 서버명, 도구명, 함수명" in prompt
    assert "현재 심사 단계" in prompt
    assert "청문 규정" in prompt
    assert "괄호로 끼워 넣지 마세요" in prompt
    assert "어려운 법률·행정 용어가 있을 때만" in prompt
    assert "허위정보, 필수정보, 표시·광고처럼 뜻이 바로 드러나는 말" in prompt
    assert "제23조(청문)" in prompt
    assert "원문 요약:" in prompt
    assert "용어 설명:" in prompt
    assert "법령 체계:" in prompt
    assert "쉬운 풀이:" in prompt
    assert "Markdown 불릿" in prompt
    assert "실제 용어명으로 시작" in prompt
    assert "청문`이 나오면" in prompt
    assert "위임·위탁`이 나오면" in prompt
    assert "과태료`가 나오면" in prompt
    assert "자연스러운 해요체" in prompt
    assert "처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차에요" in prompt
    assert "쉬운 풀이 불릿" in prompt
    assert "반복하지 마세요" in prompt
    assert "고정 접두어 없이" in prompt
    assert "### 1) 제목" in prompt
    assert "제목, 원문 요약 문단, 설명/풀이 불릿" in prompt
    assert "원문 요약 문단은 2문장" in prompt
    assert "각 변화 묶음마다 2~3개 불릿" in prompt
    assert "불릿만으로 변화 묶음을 시작하지 마세요" in prompt
    assert "짧은 명사형 항목명" in prompt
    assert "허위개발정보 유포를 금지하는 조문 신설" in prompt
    assert "인터넷 표시·광고의 필수정보와 부당한 표시를 제한" in prompt
    assert "벌칙·과태료 체계 개정과 집행주체 확충" in prompt
    assert "허위정보·부당광고 위반 시 제재 강화" in prompt
    assert "**중요 단어**" in prompt
    assert "<mark>중요 문장</mark>" in prompt
    assert "토스 앱처럼 자연스러운 `-요` 체" in prompt
    assert "`합니다`, `됩니다`, `입니다`" in prompt
    assert "짧게 쓴다는 이유로 근거, 영향, 예외를 덜어내지 마세요" in prompt
    assert "법률·행정용어 풀이 사전" in prompt
    assert "법제처 법령용어 API" in prompt
    assert "target=lstrmAI" in prompt
    assert "설명하지 않을 용어" in prompt


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


def test_agentic_report_validation_requires_term_explanation_bullets():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
- 기존 법의 제23조는 청문 규정이었으나 새 조항이 추가됩니다.
  - 사용자 입장에서는, 사후 처분 중심에서 예방 단계 관리로 바뀝니다.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "용어 설명 불릿" in str(exc) or "쉽게 말하면" in str(exc)
    else:
        raise AssertionError("용어 설명 불릿이 빠진 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_requires_hearing_term_explanation():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
- 기존 제23조는 청문 절차를 두는 조항이었지만, 새 규정이 추가됩니다.
  - 허위정보: 사실과 다르게 거래 조건을 제시한 내용입니다.
  - 사용자 입장에서는, 거래 전 정보 유통 단계도 관리한다는 뜻입니다.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "청문 용어 설명" in str(exc)
    else:
        raise AssertionError("청문 용어 설명 불릿이 빠진 리포트는 성공하면 안 됩니다.")


def test_agentic_report_validation_requires_markdown_bullets_for_explanations():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
기존 제28조는 과태료 부과 근거를 둡니다.
과태료: 행정질서 위반에 대한 금전 제재입니다.
사용자 입장에서는, 규칙을 어기면 비용 부담이 생깁니다.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "Markdown 불릿" in str(exc)
    else:
        raise AssertionError("설명 문장이 불릿이 아닌 리포트는 성공하면 안 됩니다.")


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

제25조의3에 제3항을 추가해 신고내용조사 관련 권한 위임·위탁 근거를 넓혀요.

- 위임·위탁: 행정기관이 가진 권한이나 업무 일부를 다른 기관이 맡아 처리하게 하는 방식이에요.
- 지방정부가 신고자료 검증을 더 빠르게 처리할 수 있어요.
"""

    _validate_report_body(report_body)


def test_agentic_report_validation_accepts_bolded_legal_term_labels():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
**사용자**에게 보여줄 요약이에요. <mark>핵심 변화는 거래 전 정보 확인이 쉬워지는 점이에요.</mark>

## 주요 내용
- **권한 정비**: 필요한 설명이에요.

## 무엇이 달라지나

### 1) 신고내용조사 위탁 범위 확대

제25조의3에 제3항을 추가해 신고내용조사 관련 권한 위임·위탁 근거를 넓혀요.

- **위임·위탁**: 행정기관이 가진 권한이나 업무 일부를 다른 기관이 맡아 처리하게 하는 방식이에요.
- 지방정부가 신고자료 검증을 더 빠르게 처리할 수 있어요.

### 2) 위반 시 금전 제재 강화

허위정보와 부당광고를 어기면 과태료 부과 대상이 더 분명해져요.

- **과태료**: 행정질서 위반에 부과하는 금전 제재에요.
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

허위정보와 부당광고를 어기면 **제재**가 더 분명해져요.

- 과태료: 행정질서 위반에 부과하는 금전 제재에요.
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


def test_agentic_report_validation_rejects_unnecessary_obvious_term_explanations():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
- 제23조의2를 새로 둬 허위정보 유포를 금지합니다.
  - 허위정보: 거래를 성사시키기 위해 사실이 아닌 내용으로 유포된 광고·글·영상·이미지를 말합니다.
  - 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "불필요한 용어 설명" in str(exc)
    else:
        raise AssertionError("뜻이 바로 드러나는 말까지 설명한 리포트는 성공하면 안 됩니다.")


def test_legal_term_glossary_context_uses_law_open_api_references():
    from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

    context = build_legal_term_glossary_context("청문 규정과 과태료, 허위정보 유포를 설명합니다.")

    assert "법률·행정용어 풀이 사전" in context
    assert "법제처 법령용어 API" in context
    assert "lawSearch.do?target=lstrmAI" in context
    assert "lawService.do?target=lstrmRlt" in context
    assert "lawService.do?target=dlytrmRlt" in context
    assert "청문 규정: 처분을 받기 전에" in context
    assert "과태료: 행정질서 위반" in context
    assert "허위정보" in context
    assert "설명하지 않을 용어" in context


def test_agentic_report_validation_rejects_repeated_easy_explanation_starter():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
- 기존 제28조는 과태료 부과 근거를 둡니다.
  - 과태료: 행정질서 위반에 대한 금전 제재입니다.
  - 쉽게 말하면, 규칙을 어기면 비용 부담이 생깁니다.
- 기존 제25조의3은 위임·위탁 범위를 조정합니다.
  - 위임·위탁: 행정 권한이나 업무 일부를 다른 기관에 맡기는 방식입니다.
  - 쉽게 말하면, 처리할 수 있는 기관이 늘어납니다.
"""

    try:
        _validate_report_body(report_body)
    except RuntimeError as exc:
        assert "반복" in str(exc)
    else:
        raise AssertionError("같은 쉬운 풀이 접두어가 반복된 리포트는 성공하면 안 됩니다.")


def test_codex_agent_command_includes_four_mcp_servers(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.setenv("LAW_OC", "law-key")
    monkeypatch.setenv("ASSEMBLY_API_KEY", "assembly-key")
    monkeypatch.setenv("KOSIS_API_KEY", "kosis-key")

    agent = CodexBillReportAgent(workdir="/tmp/lawdigest-agent", model="gpt-5.3-codex-spark")
    command, stdin_text = agent.build_command(
        prompt="리포트를 작성하세요.",
        output_path=str(tmp_path / "report.md"),
    )

    joined = " ".join(command)
    assert command[:2] == ["codex", "exec"]
    assert "--ignore-user-config" in command
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

    monkeypatch.setenv("ASSEMBLY_API_KEY", "assembly-key")
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


def test_codex_agent_uses_gpt_54_mini_by_default():
    from lawdigest_ai.processor.agentic_bill_report import DEFAULT_CODEX_MODEL

    assert DEFAULT_CODEX_MODEL == "gpt-5.4-mini"


def test_codex_agent_requires_assembly_api_key(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import CodexBillReportAgent

    monkeypatch.delenv("ASSEMBLY_API_KEY", raising=False)
    monkeypatch.delenv("APIKEY_billsInfo", raising=False)
    monkeypatch.delenv("APIKEY_status", raising=False)

    agent = CodexBillReportAgent()
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

    agent = CodexBillReportAgent()
    command, _ = agent.build_command(
        prompt="리포트를 작성하세요.",
        output_path=str(tmp_path / "report.md"),
    )

    assert "mcp_servers.open-assembly.env" in " ".join(command)


def test_run_agentic_bill_reports_writes_markdown_artifacts(tmp_path, monkeypatch):
    from lawdigest_ai.processor.agentic_bill_report import run_agentic_bill_reports

    monkeypatch.setenv("ASSEMBLY_API_KEY", "assembly-key")

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

    monkeypatch.setenv("ASSEMBLY_API_KEY", "assembly-key")

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

    monkeypatch.setenv("ASSEMBLY_API_KEY", "assembly-key")

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
