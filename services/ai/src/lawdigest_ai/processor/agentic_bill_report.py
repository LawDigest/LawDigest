from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_OUTPUT_DIR = "/tmp/lawdigest-bill-agent-reports"
DEFAULT_CODEX_MODEL = os.getenv("BILL_AGENT_CODEX_MODEL", "gpt-5.3-codex-spark")
DEFAULT_CODEX_BIN = os.getenv("CODEX_CLI_BIN", "codex")
DEFAULT_CODEX_TIMEOUT_SECONDS = int(os.getenv("BILL_AGENT_CODEX_TIMEOUT_SECONDS", "900"))
DEFAULT_AGENT_WORKDIR = os.getenv("BILL_AGENT_CODEX_WORKDIR", "/tmp")

PASSED_RESULT_TERMS = ("원안가결", "수정가결", "가결")
PASSED_STAGE_TERMS = ("공포", "본회의 의결")
EXCLUDED_RESULT_TERMS = ("폐기", "철회", "부결", "임기만료")


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_array(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


def _toml_inline_table(values: dict[str, str]) -> str:
    if not values:
        return "{}"
    return "{ " + ", ".join(f"{key} = {_toml_string(value)}" for key, value in values.items()) + " }"


def _slugify_bill_id(value: Any) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "bill").strip())
    return slug.strip("_") or "bill"


def _db_mode_for_execution(mode: str) -> str:
    return "prod" if mode == "prod" else "test"


def _resolve_read_mode(mode: str, read_mode: str | None) -> str:
    if read_mode:
        return read_mode
    return _db_mode_for_execution(mode)


def build_bill_report_prompt(bill: Dict[str, Any]) -> str:
    payload = {
        "bill_id": bill.get("bill_id"),
        "bill_number": bill.get("bill_number"),
        "bill_name": bill.get("bill_name"),
        "bill_result": bill.get("bill_result"),
        "stage": bill.get("stage"),
        "committee": bill.get("committee"),
        "propose_date": str(bill.get("propose_date") or ""),
        "proposers": bill.get("proposers"),
        "summary": bill.get("summary"),
        "bill_link": bill.get("bill_link"),
        "bill_pdf_url": bill.get("bill_pdf_url"),
    }
    return (
        "당신은 Lawdigest의 국회 법률개정안 리서치 에이전트입니다.\n"
        "아래 입력은 이미 통과된 법안 후보입니다. 단, 실제 처리 결과와 통과 경로는 반드시 도구로 다시 확인하세요.\n\n"
        "목표: MCP 도구를 능동적으로 사용해 해당 법안에 대한 종합적인 한국어 리포트를 작성하세요.\n"
        "반드시 사용할 MCP 서버와 역할:\n"
        "- open-assembly: 법안 상세, 심사경과, 발의자, 위원회, 표결, 본회의/위원회 흐름 확인\n"
        "- assembly-api: 국회 원천 API 보완 조회, 입법 라이프사이클, NABO/국민참여입법센터 관련 자료 탐색\n"
        "- korean-law: 현행법 및 개정 법령 맥락, 관련 조문, 법령 인용 검증, 시점 비교\n"
        "- korean-stats: 통계청 공식 통계가 정책 배경 설명에 의미 있는 경우만 수치와 출처 확인\n\n"
        "리포트에는 다음 섹션을 포함하세요:\n"
        "1. 핵심 결론\n"
        "2. 법안의 통과 경로\n"
        "3. 개정 전후 법제 맥락\n"
        "4. 정책 배경과 통계 근거\n"
        "5. 이해관계자와 집행 영향\n"
        "6. 쟁점, 한계, 후속 모니터링 포인트\n"
        "7. Lawdigest 요약 개선 제안\n"
        "8. 사용한 MCP 도구와 출처\n\n"
        "작성 규칙:\n"
        "- 도구 조회 없이 추정으로 단정하지 마세요.\n"
        "- 통계청 공식 통계가 관련성이 낮으면 '관련 공식 통계 근거는 제한적'이라고 쓰고 억지로 숫자를 만들지 마세요.\n"
        "- 법령명, 의안번호, 처리결과, 날짜, 위원회명은 도구 결과와 입력이 다르면 도구 결과를 우선하세요.\n"
        "- 최종 출력은 Markdown만 작성하세요.\n\n"
        f"입력 법안 payload:\n{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"
    )


def _fetch_passed_bills(mode: str, limit: int, read_mode: str | None = None) -> List[Dict[str, Any]]:
    from lawdigest_ai.db import get_db_connection

    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")

    db_mode = _resolve_read_mode(mode, read_mode)
    result_filters = " OR ".join(["bill_result LIKE %s" for _ in PASSED_RESULT_TERMS])
    stage_filters = " OR ".join(["stage LIKE %s" for _ in PASSED_STAGE_TERMS])
    excluded_filters = " AND ".join([f"COALESCE(bill_result, '') NOT LIKE %s" for _ in EXCLUDED_RESULT_TERMS])
    query = f"""
    SELECT
        bill_id,
        bill_number,
        bill_name,
        summary,
        proposers,
        proposer_kind,
        propose_date,
        stage,
        committee,
        bill_result,
        bill_link,
        bill_pdf_url
    FROM Bill
    WHERE
        summary IS NOT NULL
        AND summary != ''
        AND ({result_filters} OR {stage_filters})
        AND {excluded_filters}
    ORDER BY propose_date DESC
    LIMIT %s
    """
    params: list[Any] = (
        [f"%{term}%" for term in PASSED_RESULT_TERMS]
        + [f"%{term}%" for term in PASSED_STAGE_TERMS]
        + [f"%{term}%" for term in EXCLUDED_RESULT_TERMS]
        + [limit]
    )

    conn = get_db_connection(mode=db_mode)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return list(cur.fetchall())
    finally:
        conn.close()


@dataclass(frozen=True)
class CodexBillReportAgent:
    cli_bin: str = DEFAULT_CODEX_BIN
    model: str = DEFAULT_CODEX_MODEL
    timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS
    workdir: str = DEFAULT_AGENT_WORKDIR

    def _mcp_server_config_args(self) -> list[str]:
        assembly_key = os.getenv("ASSEMBLY_API_KEY") or "sample"
        law_oc = os.getenv("LAW_OC", "")
        kosis_key = os.getenv("KOSIS_API_KEY", "")
        config: dict[str, dict[str, Any]] = {
            "korean-stats": {
                "command": "npx",
                "args": ["-y", "mcp-remote", "https://korean-stats-mcp.fly.dev/mcp"],
                "env": {"KOSIS_API_KEY": kosis_key} if kosis_key else {},
            },
            "korean-law": {
                "command": "npx",
                "args": ["-y", "korean-law-mcp@latest"],
                "env": {"LAW_OC": law_oc} if law_oc else {},
            },
            "assembly-api": {
                "command": "npx",
                "args": ["-y", "assembly-api-mcp@latest"],
                "env": {
                    "ASSEMBLY_API_KEY": assembly_key,
                    "MCP_PROFILE": "full",
                    "MCP_TRANSPORT": "stdio",
                },
            },
            "open-assembly": {
                "command": "uvx",
                "args": ["open-assembly-mcp@latest"],
                "env": {"ASSEMBLY_API_KEY": assembly_key},
            },
        }

        args: list[str] = []
        for server_name, server in config.items():
            prefix = f"mcp_servers.{server_name}"
            args.extend(["-c", f"{prefix}.command={_toml_string(server['command'])}"])
            args.extend(["-c", f"{prefix}.args={_toml_array(server['args'])}"])
            if server.get("env"):
                args.extend(["-c", f"{prefix}.env={_toml_inline_table(server['env'])}"])
        return args

    def build_command(self, *, prompt: str, output_path: str) -> tuple[list[str], str]:
        command = [
            self.cli_bin,
            "exec",
            "--sandbox",
            "read-only",
            "--cd",
            self.workdir,
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-rules",
            "--model",
            self.model,
            "--output-last-message",
            output_path,
            *self._mcp_server_config_args(),
            "-",
        ]
        return command, prompt

    def write_report(self, *, bill: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        prompt = build_bill_report_prompt(bill)
        command, stdin_text = self.build_command(prompt=prompt, output_path=output_path)
        report_path = Path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        proc = subprocess.run(
            command,
            input=stdin_text,
            capture_output=True,
            text=True,
            cwd=self.workdir,
            timeout=self.timeout_seconds,
        )
        stdout_text = (proc.stdout or "").strip()
        if proc.returncode != 0:
            error = (proc.stderr or stdout_text or "Codex agent failed").strip()
            raise RuntimeError(error)
        if not report_path.exists() and stdout_text:
            report_path.write_text(stdout_text, encoding="utf-8")
        if not report_path.exists() or not report_path.read_text(encoding="utf-8").strip():
            raise RuntimeError("Codex agent report body is empty.")

        return {
            "bill_id": bill.get("bill_id"),
            "bill_name": bill.get("bill_name"),
            "report_path": str(report_path),
            "status": "success",
        }


def run_agentic_bill_reports(
    *,
    mode: str = "dry_run",
    limit: int = 5,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    read_mode: str | None = None,
    codex_model: str | None = None,
    stop_on_error: bool = False,
) -> Dict[str, Any]:
    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")

    targets = _fetch_passed_bills(mode=mode, limit=limit, read_mode=read_mode)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    agent = CodexBillReportAgent(model=codex_model or DEFAULT_CODEX_MODEL)
    items: list[dict[str, Any]] = []

    for target in targets:
        bill_id = target.get("bill_id")
        report_path = output_root / f"{_slugify_bill_id(bill_id)}.md"
        try:
            items.append(agent.write_report(bill=target, output_path=str(report_path)))
        except Exception as exc:
            failed = {
                "bill_id": bill_id,
                "bill_name": target.get("bill_name"),
                "report_path": str(report_path),
                "status": "failed",
                "error": str(exc),
            }
            items.append(failed)
            if stop_on_error:
                raise

    report = {
        "execution_mode": mode,
        "read_mode": _resolve_read_mode(mode, read_mode),
        "provider": "codex-agent",
        "model": codex_model or DEFAULT_CODEX_MODEL,
        "target": "passed_bills",
        "output_dir": str(output_root),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "target_count": len(targets),
            "processed_count": len(items),
            "success_count": sum(1 for item in items if item["status"] == "success"),
            "failure_count": sum(1 for item in items if item["status"] == "failed"),
        },
        "items": items,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return report
