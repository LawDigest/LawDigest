from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from lawdigest_ai.processor.legal_term_glossary import build_legal_term_glossary_context

DEFAULT_OUTPUT_DIR = "/tmp/lawdigest-bill-agent-reports"
DEFAULT_CODEX_MODEL = os.getenv("BILL_AGENT_CODEX_MODEL", "gpt-5.3-codex-spark")
DEFAULT_CODEX_BIN = os.getenv("CODEX_CLI_BIN", "codex")
DEFAULT_CODEX_TIMEOUT_SECONDS = int(os.getenv("BILL_AGENT_CODEX_TIMEOUT_SECONDS", "900"))
DEFAULT_AGENT_WORKDIR = os.getenv("BILL_AGENT_CODEX_WORKDIR", "/tmp")

PASSED_RESULT_TERMS = ("원안가결", "수정가결", "가결")
PASSED_STAGE_TERMS = ("공포", "본회의 의결")
EXCLUDED_RESULT_TERMS = ("폐기", "철회", "부결", "임기만료")
MCP_APPROVED_TOOLS = {
    "korean-stats": (
        "search_statistics",
        "get_statistics_list",
        "get_statistics_data",
        "compare_statistics",
        "analyze_time_series",
        "get_table_info",
        "quick_stats",
        "quick_trend",
        "quick_rank",
        "explain_statistic",
        "fetch_kosis_excel",
        "chain_region_brief",
        "chain_compare_regions",
        "chain_policy_indicator",
    ),
    "korean-law": (
        "search_law",
        "get_law_text",
        "get_annexes",
        "legal_research",
        "legal_analysis",
        "discover_tools",
        "execute_tool",
        "get_legal_term_kb",
        "get_legal_term_detail",
        "get_daily_term",
        "get_daily_to_legal",
        "get_legal_to_daily",
        "get_term_articles",
        "search_decisions",
        "get_decision_text",
    ),
    "open-assembly": (
        "search_bills",
        "get_bill_detail",
        "get_member_info",
        "get_vote_results",
        "get_bill_review",
        "get_bill_proposers",
        "get_member_votes",
        "get_committee_members",
        "get_pending_bills",
        "get_plenary_agenda",
        "get_bill_committee_review",
        "get_bill_summary",
        "analyze_legislator",
        "get_party_cohesion",
        "search_nars_reports",
        "search_petitions",
        "get_schedule",
        "search_hearings",
        "discover_apis",
        "query_assembly",
    ),
    "assembly-api": (
        "assembly_member",
        "assembly_bill",
        "assembly_session",
        "assembly_org",
        "discover_apis",
        "query_assembly",
        "bill_detail",
        "committee_detail",
        "petition_detail",
        "research_data",
    ),
}


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
    payload_text = json.dumps(payload, ensure_ascii=False, default=str)
    legal_term_context = build_legal_term_glossary_context(payload_text)
    return (
        "당신은 Lawdigest의 법안 리포트 작성자입니다.\n"
        "아래 입력은 이미 통과된 법안 후보입니다. MCP 도구를 능동적으로 사용해 사실관계를 확인하되, 출력은 내부 조사 로그가 아니라 "
        "사용자에게 보여줄 최종 법안 리포트여야 합니다.\n\n"
        "조사 원칙:\n"
        "- open-assembly와 assembly-api로 법안명, 의안번호, 처리결과, 법안의 통과 경로, 위원회, 표결 정보를 확인하세요.\n"
        "- korean-law로 현행법 및 개정 법령 맥락, 관련 조문, 법령 인용 검증, 시점 비교를 확인하세요.\n"
        "- korean-stats는 정책 배경 설명에 직접 도움이 되는 공식 통계가 있을 때만 사용하세요.\n"
        "- 도구 결과가 입력과 다르면 도구 결과를 우선하되, 불확실한 내용은 단정하지 마세요.\n\n"
        "출력 형식:\n"
        "# 법안명\n"
        "## 쉬운 요약\n"
        "- 법안이 무엇을 바꾸는지 3~5문장으로 설명하세요. 토스 앱처럼 짧고 쉽게 쓰되 내용을 덜어내지 마세요.\n"
        "- 본회의 표결수, 현재 심사 단계, 공포일 같은 상태값은 프론트엔드 데이터가 따로 보여주므로 요약 본문에 쓰지 마세요.\n"
        "## 주요 내용\n"
        "- 여러 제도가 함께 바뀌는 법안이면 4~6개 항목을 쓰세요.\n"
        "- 각 항목은 반드시 `항목 제목: 쉬운 설명` 형식으로 쓰세요.\n"
        "- `핵심:` 또는 `설명:` 같은 메타 라벨을 그대로 출력하지 마세요.\n"
        "## 왜 나왔나\n"
        "- 제안 이유와 정책 배경을 사용자 관점에서 설명하세요.\n"
        "## 무엇이 달라지나\n"
        "- 현행법과 달라지는 점을 구체적으로 쓰되, 각 변화 묶음은 반드시 제목, 원문 요약 문단, 설명/풀이 불릿 순서로 쓰세요.\n"
        "- 각 변화 묶음은 반드시 `### 1) 제목`, `### 2) 제목`처럼 번호 헤딩으로 시작하세요.\n"
        "- 제목은 설명문이 아니라 짧은 명사형 항목명으로 쓰세요.\n"
        "- 예를 들어 `허위개발정보 유포를 금지하는 조문을 새로 둔다`가 아니라 `허위개발정보 유포를 금지하는 조문 신설`로 쓰세요.\n"
        "- `인터넷 표시·광고의 필수정보와 부당한 표시를 제한한다`가 아니라 `인터넷 표시·광고의 필수정보와 부당한 표시를 제한`으로 쓰세요.\n"
        "- 번호 헤딩 다음에는 불릿이 아닌 일반 문단으로 원문 조문 변화의 요약을 1문단 쓰세요.\n"
        "- 그 아래에 필요한 설명/풀이를 Markdown 불릿(`- ...`)으로 붙이세요.\n"
        "- 불릿만으로 변화 묶음을 시작하지 마세요.\n"
        "- 청문 규정, 과태료, 위임·위탁, 조문 체계처럼 일반 사용자가 모를 법한 법률·행정 용어는 괄호로 끼워 넣지 마세요.\n"
        "- `제23조(청문)`처럼 출처식 괄호 표기를 본문에 옮기지 마세요. 본문에 청문을 언급해야 하면 별도 `청문 규정:` 불릿으로 설명하세요.\n"
        "- `- 실제 용어명으로 시작하는 설명 불릿`은 어려운 법률·행정 용어가 있을 때만 중간에 붙이세요.\n"
        "- 용어 설명과 쉬운 풀이 문장은 반드시 Markdown 불릿(`- ...`)으로 쓰세요.\n"
        "- 첫 문장에 `원문 요약:` 같은 메타 라벨을 붙이지 말고 바로 조문 변화 문장을 쓰세요.\n"
        "- 용어 설명 불릿은 `용어 설명:`이나 `법령 체계:` 같은 메타 라벨을 쓰지 말고, 반드시 실제 용어명으로 시작하세요. 예: `청문 규정:`, `과태료:`, `위임·위탁:`\n"
        "- 쉬운 풀이 불릿도 `쉬운 풀이:` 같은 메타 라벨을 쓰지 마세요.\n"
        "- 허위정보, 필수정보, 표시·광고처럼 뜻이 바로 드러나는 말은 사전식 용어 설명 불릿을 붙이지 마세요. 그런 경우에는 바로 사용자에게 어떤 변화가 생기는지 쉬운 풀이로 넘어가세요.\n"
        "- 원문 요약 문장에 `청문`이 나오면 바로 아래에 반드시 `청문 규정:` 또는 `청문 절차:` 설명 불릿을 붙이세요.\n"
        "- 원문 요약 문장에 `위임·위탁`이 나오면 바로 아래에 반드시 `위임·위탁:` 설명 불릿을 붙이세요.\n"
        "- 원문 요약 문장에 `과태료`가 나오면 바로 아래에 반드시 `과태료:` 설명 불릿을 붙이세요.\n"
        "- 쉬운 풀이 불릿은 사용자에게 말하듯 자연스러운 해요체로 쓰되, `쉽게 말하면,` 같은 고정 접두어를 반복하지 마세요.\n"
        "- 쉬운 풀이 불릿은 고정 접두어 없이 바로 풀어 써도 됩니다. 문장 시작은 항목의 내용에 맞게 자연스럽게 바꾸세요.\n"
        "- 예:\n"
        "  ### 1) 온라인 유통질서 규율 조항군 신설\n\n"
        "  기존 조문 체계에서 제23조는 주로 허가 취소 절차의 청문 규정이었으나, 제안안은 이를 온라인 유통질서 규율 조항군으로 넓힙니다.\n\n"
        "  - 청문 규정: 여기서 `청문`은 처분을 받기 전에 당사자가 설명하고 반론할 수 있는 절차에요.\n"
        "  - 사용자 입장에서는, 문제가 터진 뒤에 벌을 주는 데서 그치지 않고 거래 전에 정보가 맞는지 더 일찍 걸러내겠다는 뜻이에요.\n"
        "## 누구에게 영향이 있나\n"
        "- 영향을 받는 사람과 기관을 나누어 설명하세요.\n"
        "## 봐야 할 점\n"
        "- 시행 전 확인할 쟁점, 집행상 한계, 후속 모니터링 포인트를 적으세요.\n"
        "## 확인한 근거\n"
        "- 국회, 법제처, 통계청 등 기관명과 확인한 문서·항목만 짧게 적으세요.\n"
        "- MCP 서버명, 도구명, 함수명, 호출 결과명은 쓰지 마세요.\n\n"
        "작성 규칙:\n"
        "- 내부 조사 과정, MCP 도구 호출 목록, 실패 로그, 리서치 메모를 본문에 쓰지 마세요.\n"
        "- 운영자용 개선 제안 섹션을 만들지 마세요.\n"
        "- 통계청 공식 통계가 관련성이 낮으면 숫자를 억지로 만들지 말고, 필요한 경우 한 문장으로만 한계를 밝히세요.\n"
        "- 동어반복, 과장, 번역투를 피하고 짧은 문장을 우선하세요.\n"
        "- 문체는 토스 앱처럼 자연스러운 `-요` 체로 쓰세요.\n"
        "- `합니다`, `됩니다`, `입니다`, `바뀝니다` 같은 `-니다` 체 종결을 쓰지 마세요.\n"
        "- `줄어드어요`처럼 어색한 변환을 쓰지 말고 `줄어들어요`처럼 자연스럽게 쓰세요.\n"
        "- 독자가 바로 봐야 할 **중요 단어**에는 Markdown 볼드체를 적용하세요.\n"
        "- 결론이나 행동 변화처럼 중요한 한 문장에는 `<mark>중요 문장</mark>` 형식으로 하이라이트를 적용하세요.\n"
        "- 볼드체와 하이라이트는 과하게 쓰지 말고, 리포트 전체에서 꼭 필요한 곳에만 쓰세요.\n"
        "- 최종 출력은 Markdown만 작성하세요.\n\n"
        f"{legal_term_context}\n\n"
        f"입력 법안 payload:\n{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"
    )


def _markdown_section_body(body: str, heading: str) -> str:
    start = body.find(heading)
    if start == -1:
        return body
    section_start = start + len(heading)
    next_heading = body.find("\n## ", section_start)
    if next_heading == -1:
        return body[section_start:]
    return body[section_start:next_heading]


def _validate_report_body(report_body: str) -> None:
    body = report_body.strip()
    if not body:
        raise RuntimeError("Codex agent report body is empty.")

    required_headings = ("## 쉬운 요약", "## 주요 내용")
    missing_headings = [heading for heading in required_headings if heading not in body]
    if missing_headings:
        raise RuntimeError("생성 리포트에 필수 섹션이 없습니다: " + ", ".join(missing_headings))

    forbidden_patterns = (
        "Lawdigest 요약 개선 제안",
        "사용한 MCP 도구",
        "MCP 도구",
        "원문 요약:",
        "용어 설명:",
        "법령 체계:",
        "쉬운 풀이:",
        "mcp__",
        "`get_",
        "`search_",
        "`legal_",
        "`query_",
        "내부 조사",
        "리서치 메모",
    )
    leaked_patterns = [pattern for pattern in forbidden_patterns if pattern in body]
    if leaked_patterns:
        raise RuntimeError("생성 리포트에 내부 조사 표현이 남아 있습니다: " + ", ".join(leaked_patterns))

    changes_body = _markdown_section_body(body, "## 무엇이 달라지나")
    explanation_terms = ("청문 규정", "과태료", "위임·위탁")
    missing_explanations = [term for term in explanation_terms if term in changes_body and f"{term}:" not in changes_body]
    if missing_explanations:
        raise RuntimeError("생성 리포트에 용어 설명 불릿이 없습니다: " + ", ".join(missing_explanations))

    if "청문" in changes_body and all(label not in changes_body for label in ("청문 규정:", "청문 절차:", "청문:")):
        raise RuntimeError("생성 리포트에 청문 용어 설명 불릿이 없습니다.")

    repeated_starters = ("쉽게 말하면,", "쉽게 말해,", "한마디로,")
    repeated = [starter for starter in repeated_starters if changes_body.count(starter) > 1]
    if repeated:
        raise RuntimeError("생성 리포트의 쉬운 풀이 문장 시작이 반복됩니다: " + ", ".join(repeated))

    unnecessary_definition_labels = ("허위정보:", "허위정보 유포:", "필수정보:", "표시·광고:")
    unnecessary_definitions = [label for label in unnecessary_definition_labels if label in changes_body]
    if unnecessary_definitions:
        raise RuntimeError("생성 리포트에 불필요한 용어 설명 불릿이 있습니다: " + ", ".join(unnecessary_definitions))

    easy_starters = repeated_starters + ("사용자 입장에서는,", "바뀌는 점은,", "실제로는,", "이 말은", "결국")
    unbulleted_easy_starters = [
        starter
        for starter in easy_starters
        if starter in changes_body
        and f"\n- {starter}" not in changes_body
        and f"\n  - {starter}" not in changes_body
    ]
    if unbulleted_easy_starters:
        raise RuntimeError(
            "생성 리포트의 쉬운 풀이 문장은 Markdown 불릿이어야 합니다: "
            + ", ".join(unbulleted_easy_starters)
        )

    term_labels = ("청문 규정:", "청문 절차:", "청문:", "과태료:", "위임·위탁:")
    unbulleted_labels = [
        label
        for label in term_labels
        if label in changes_body and f"\n- {label}" not in changes_body and f"\n  - {label}" not in changes_body
    ]
    if unbulleted_labels:
        raise RuntimeError("생성 리포트의 용어 설명 문장은 Markdown 불릿이어야 합니다: " + ", ".join(unbulleted_labels))

    if changes_body.strip() and not re.search(r"(?m)^### 1\)\s+\S", changes_body):
        raise RuntimeError("생성 리포트의 변화 설명은 번호 헤딩 형식이어야 합니다.")

    sentence_style_headings = [
        heading
        for heading in re.findall(r"(?m)^###\s+\d+\)\s+(.+)$", changes_body)
        if re.search(r"(한다|둔다|넓힌다|바꾼다|늘린다|줄인다)$", heading.strip())
    ]
    if sentence_style_headings:
        raise RuntimeError("생성 리포트의 변화 제목은 짧은 명사형 제목이어야 합니다: " + ", ".join(sentence_style_headings))

    if not re.search(r"\*\*[^*\n][^*\n]*\*\*", body):
        raise RuntimeError("생성 리포트에 중요 단어 볼드체가 없습니다.")

    if not re.search(r"<mark>[^<>\n]+</mark>", body):
        raise RuntimeError("생성 리포트에 중요 문장 하이라이트가 없습니다.")

    remaining_formal_endings = sorted(set(re.findall(r"[가-힣]+니다\.", body)))
    if remaining_formal_endings:
        raise RuntimeError("생성 리포트에 토스식 -요 체가 아닌 격식체 종결이 남아 있습니다: " + ", ".join(remaining_formal_endings))

    awkward_yo_tone = ("줄어드어요",)
    awkward_matches = [phrase for phrase in awkward_yo_tone if phrase in body]
    if awkward_matches:
        raise RuntimeError("생성 리포트에 어색한 -요 체가 남아 있습니다: " + ", ".join(awkward_matches))


def _fetch_passed_bills(mode: str, limit: int, read_mode: str | None = None) -> List[Dict[str, Any]]:
    from lawdigest_ai.db import get_db_connection

    if limit < 1:
        raise ValueError("limit는 1 이상이어야 합니다.")

    db_mode = _resolve_read_mode(mode, read_mode)
    result_filters = " OR ".join(["bill_result LIKE %s" for _ in PASSED_RESULT_TERMS])
    stage_filters = " OR ".join(["stage LIKE %s" for _ in PASSED_STAGE_TERMS])
    excluded_filters = " AND ".join(["COALESCE(bill_result, '') NOT LIKE %s" for _ in EXCLUDED_RESULT_TERMS])
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
        assembly_key = os.getenv("ASSEMBLY_API_KEY") or os.getenv("APIKEY_billsInfo") or os.getenv("APIKEY_status")
        if not assembly_key:
            raise RuntimeError("ASSEMBLY_API_KEY 환경변수가 필요합니다.")
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
            for tool_name in MCP_APPROVED_TOOLS.get(server_name, ()):
                args.extend(["-c", f"{prefix}.tools.{tool_name}.approval_mode={_toml_string('approve')}"])
        return args

    def build_command(self, *, prompt: str, output_path: str) -> tuple[list[str], str]:
        command = [
            self.cli_bin,
            "exec",
            "--ignore-user-config",
            "--disable",
            "plugins",
            "--disable",
            "apps",
            "--disable",
            "memories",
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
        if not report_path.exists():
            raise RuntimeError("Codex agent report body is empty.")
        _validate_report_body(report_path.read_text(encoding="utf-8"))

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
