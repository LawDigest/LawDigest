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

    assert "통과된 법안" in prompt
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
    assert "항목 제목: 쉬운 설명" in prompt
    assert "Lawdigest 요약 개선 제안" not in prompt
    assert "사용한 MCP 도구와 출처" not in prompt
    assert "내부 조사 로그" in prompt
    assert "MCP 서버명, 도구명, 함수명" in prompt
    assert "현재 심사 단계" in prompt
    assert "청문 규정" in prompt
    assert "괄호로 끼워 넣지 마세요" in prompt
    assert "어려운 법률·행정 용어가 있을 때만" in prompt
    assert "허위정보, 필수정보, 표시·광고처럼 뜻이 바로 드러나는 말" in prompt
    assert "원문 요약:" in prompt
    assert "용어 설명:" in prompt
    assert "법령 체계:" in prompt
    assert "실제 용어명으로 시작" in prompt
    assert "청문`이 나오면" in prompt
    assert "위임·위탁`이 나오면" in prompt
    assert "과태료`가 나오면" in prompt
    assert "자연스러운 해요체" in prompt
    assert "처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차에요" in prompt
    assert "쉬운 풀이 불릿" in prompt
    assert "반복하지 마세요" in prompt
    assert "고정 접두어 없이" in prompt


def test_agentic_report_validation_rejects_internal_tool_leaks():
    from lawdigest_ai.processor.agentic_bill_report import _validate_report_body

    report_body = """
# 테스트법 일부개정법률안

## 쉬운 요약
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

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
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

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
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

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
사용자에게 보여줄 요약입니다.

## 주요 내용
- 권한 정비: 필요한 설명입니다.

## 무엇이 달라지나
- 제23조의2를 새로 둬 허위정보 유포를 금지합니다.
  - 거래 전 단계에서 정보 자체를 더 엄격하게 보겠다는 뜻이에요.

## 확인한 근거
- 법제처: 제23조(청문), 제25조의3(권한 등의 위임 및 위탁), 제28조(과태료)
"""

    _validate_report_body(report_body)


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
    assert "--output-last-message" in command
    assert stdin_text == "리포트를 작성하세요."
    assert "mcp_servers.korean-stats.command" in joined
    assert "mcp_servers.korean-law.command" in joined
    assert "mcp_servers.assembly-api.command" in joined
    assert "mcp_servers.open-assembly.command" in joined
    assert "mcp_servers.korean-law.tools.search_law.approval_mode" in joined
    assert "mcp_servers.korean-stats.tools.search_statistics.approval_mode" in joined
    assert "mcp_servers.open-assembly.tools.search_bills.approval_mode" in joined
    assert "mcp_servers.assembly-api.tools.discover_apis.approval_mode" in joined
    assert "korean-law-mcp@latest" in joined
    assert "assembly-api-mcp@latest" in joined
    assert "open-assembly-mcp@latest" in joined


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
        "lawdigest_ai.processor.agentic_bill_report._fetch_passed_bills",
        return_value=[target],
    ), patch("lawdigest_ai.processor.agentic_bill_report.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout="# 테스트법 일부개정법률안\n\n## 쉬운 요약\n본문\n\n## 주요 내용\n- 권한 정비: 설명\n",
            stderr="",
        )
        result = run_agentic_bill_reports(
            mode="dry_run",
            limit=1,
            output_dir=str(tmp_path),
        )

    assert result["stats"]["target_count"] == 1
    assert result["stats"]["success_count"] == 1
    assert result["items"][0]["status"] == "success"
    report_path = Path(result["items"][0]["report_path"])
    assert report_path.exists()
    assert "쉬운 요약" in report_path.read_text(encoding="utf-8")
