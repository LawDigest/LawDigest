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
    assert "쉽게 말하면" in prompt


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
