from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from lawdigest_ai.config import (
    CLAUDE_CLI_BIN,
    CLAUDE_CLI_HOME,
    CLAUDE_CLI_MODEL,
    CLAUDE_CLI_TIMEOUT_SECONDS,
    CLAUDE_CLI_WORKDIR,
    CODEX_CLI_BIN,
    CODEX_CLI_HOME,
    CODEX_CLI_MODEL,
    CODEX_CLI_TIMEOUT_SECONDS,
    CODEX_CLI_WORKDIR,
    GEMINI_CLI_APPROVAL_MODE,
    GEMINI_CLI_BIN,
    GEMINI_CLI_HOME,
    GEMINI_CLI_MODEL,
    GEMINI_CLI_TIMEOUT_SECONDS,
    GEMINI_CLI_WORKDIR,
)
from lawdigest_ai.processor.summary_prompt_templates import (
    SUMMARY_GPT_FIELD_DESC,
    SUMMARY_LIST_GUIDELINE,
    build_proposer_opening_line,
)
from lawdigest_ai.observability import trace_generation, trace_span


CliProviderName = Literal["gemini", "codex", "claude"]


@dataclass(frozen=True)
class CliProviderConfig:
    provider: CliProviderName
    cli_bin: str
    model: str
    timeout_seconds: int
    cli_home: str | None
    cli_workdir: str
    approval_mode: str = "yolo"


def _provider_config(provider: str) -> CliProviderConfig:
    normalized = provider.strip().lower()
    if normalized == "gemini":
        return CliProviderConfig(
            provider="gemini",
            cli_bin=GEMINI_CLI_BIN,
            model=GEMINI_CLI_MODEL,
            timeout_seconds=GEMINI_CLI_TIMEOUT_SECONDS,
            cli_home=GEMINI_CLI_HOME,
            cli_workdir=GEMINI_CLI_WORKDIR,
            approval_mode=GEMINI_CLI_APPROVAL_MODE,
        )
    if normalized == "codex":
        return CliProviderConfig(
            provider="codex",
            cli_bin=CODEX_CLI_BIN,
            model=CODEX_CLI_MODEL,
            timeout_seconds=CODEX_CLI_TIMEOUT_SECONDS,
            cli_home=CODEX_CLI_HOME,
            cli_workdir=CODEX_CLI_WORKDIR,
        )
    if normalized == "claude":
        return CliProviderConfig(
            provider="claude",
            cli_bin=CLAUDE_CLI_BIN,
            model=CLAUDE_CLI_MODEL,
            timeout_seconds=CLAUDE_CLI_TIMEOUT_SECONDS,
            cli_home=CLAUDE_CLI_HOME,
            cli_workdir=CLAUDE_CLI_WORKDIR,
        )
    raise ValueError("cli_provider는 gemini, codex, claude 중 하나여야 합니다.")


class StructuredBillSummary(BaseModel):
    brief_summary: str = Field(description="법안 핵심을 한 문장으로 요약한 짧은 제목형 요약문")
    gpt_summary: str = Field(description=SUMMARY_GPT_FIELD_DESC)
    tags: list[str] = Field(min_length=5, max_length=5, description="법안 주제를 나타내는 짧은 한국어 태그 5개")


class GeminiCliSummarizer:
    def __init__(self, provider: str = "gemini"):
        config = _provider_config(provider)
        self.failed_bills: List[dict] = []
        self.logger = logging.getLogger(__name__)
        self.provider = config.provider
        self.cli_bin = config.cli_bin
        self.model = config.model
        self.timeout_seconds = config.timeout_seconds
        self.approval_mode = config.approval_mode
        self.cli_home = config.cli_home
        self.cli_workdir = config.cli_workdir
        self.debug_log_path = os.getenv(f"{self.provider.upper()}_CLI_DEBUG_LOG_PATH")
        self.style_prompt = (
            "법률개정안 텍스트에서 달라지는 핵심 내용을 항목별로 정리하세요. "
            "각 항목은 이해하기 쉬운 공식 문체로 작성하고, 3~7개 항목을 권장합니다."
        )

    def _build_user_prompt(self, row: Dict[str, Any]) -> str:
        proposer_opening = build_proposer_opening_line(
            row.get("proposers"),
            row.get("bill_name") or "법안명 미상",
        )
        intro = (
            "당신은 대한민국 법안 요약 전문가입니다. 반드시 structured output 스키마에 맞춰 응답하세요.\n\n"
            f"[법안명] {row.get('bill_name') or '법안명 미상'}\n"
            f"[발의주체] {row.get('proposer_kind') or ''}\n"
            f"[발의자] {row.get('proposers') or '발의자 미상'}\n"
            f"[발의일] {row.get('proposeDate') or row.get('propose_date') or ''}\n"
            f"[단계] {row.get('stage') or ''}\n"
        )
        task = (
            f"{self.style_prompt}\n"
            "도구를 사용하지 말고, 제공된 텍스트만 보고 응답하세요.\n"
            "반드시 JSON 객체만 응답하세요.\n"
            "키는 brief_summary, gpt_summary, tags 세 개만 포함하세요.\n"
            "운영 DB에 저장된 기존 OpenAI 요약 스타일에 최대한 가깝게 작성하세요.\n"
            "1) brief_summary: 한 문장 제목형 요약\n"
            "- 설명문이 아니라 법안 제목처럼 작성하세요.\n"
            "- 가능하면 '...을/를 위한 [법안명]' 또는 '... 도입 [법안명]'처럼 실제 법안명을 포함하세요.\n"
            "- 길이는 기존 DB처럼 다소 구체적으로 쓰되, '입니다', '합니다' 같은 종결형 문장은 쓰지 마세요.\n"
            "2) gpt_summary: 핵심 변경사항 상세 요약\n"
            "  a. 첫 문장: 해당 법안 요약은 정확히 아래 형식으로 시작하세요.\n"
            f"     \"{proposer_opening}\"\n"
            f"  b. 본문: {SUMMARY_LIST_GUIDELINE} 항목 형식으로 작성하고, 형식은 '1) ...', '2) ...'를 사용하세요.\n"
            "  c. 마지막 문단: '이 법안의 취지는 ...' 형태의 한 단락을 추가하세요.\n"
            "- '-' bullet 형식은 사용하지 마세요.\n"
            "- 번호 목록 사이에는 빈 줄을 넣어 기존 DB 스타일과 유사하게 작성하세요.\n"
            "- 핵심 용어는 필요할 때만 **굵게** 표시하세요.\n"
            "3) tags: 한국어 태그 정확히 5개 (중복 금지, 각 2~12자)\n"
        )
        return f"{intro}\n[원문 요약]\n{row.get('summary') or ''}\n\n{task}"

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @staticmethod
    def _extract_first_json_object(text: str) -> Optional[str]:
        start = text.find("{")
        if start < 0:
            return None
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
                continue
            if char == "{":
                depth += 1
                continue
            if char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]
        return None

    def _append_debug_log(self, label: str, payload: str) -> None:
        if not self.debug_log_path:
            return
        try:
            with open(self.debug_log_path, "a", encoding="utf-8") as handle:
                handle.write(f"[{label}] {payload}\n")
        except Exception:
            pass

    def _extract_json_summary(self, raw_text: str) -> StructuredBillSummary:
        cleaned = self._strip_code_fences(raw_text)
        try:
            payload = json.loads(cleaned)
            if isinstance(payload, dict) and isinstance(payload.get("response"), str):
                payload = json.loads(payload["response"])
        except json.JSONDecodeError as exc:
            json_object = self._extract_first_json_object(cleaned)
            if not json_object:
                raise ValueError(f"{self.provider} CLI 응답이 JSON이 아닙니다: {cleaned[:300]}") from exc
            payload = json.loads(json_object)
            if isinstance(payload, dict) and isinstance(payload.get("response"), str):
                payload = json.loads(payload["response"])
        try:
            return StructuredBillSummary.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"{self.provider} CLI 구조화 응답 검증 실패: {exc}") from exc

    def _build_headless_command(
        self,
        prompt: str,
        requested_model: str,
        output_path: str | None,
    ) -> tuple[List[str], str | None]:
        if self.provider == "gemini":
            command = [
                self.cli_bin,
                "--prompt",
                prompt,
                "--approval-mode",
                self.approval_mode,
                "--output-format",
                "text",
            ]
            if requested_model:
                command.extend(["--model", requested_model])
            return command, None

        if self.provider == "codex":
            command = [
                self.cli_bin,
                "exec",
                "--sandbox",
                "read-only",
                "--cd",
                self.cli_workdir,
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-rules",
            ]
            if requested_model:
                command.extend(["--model", requested_model])
            if output_path:
                command.extend(["--output-last-message", output_path])
            command.append("-")
            return command, prompt

        command = [
            self.cli_bin,
            "--print",
            "--output-format",
            "text",
            "--permission-mode",
            "dontAsk",
            "--no-session-persistence",
            "--tools",
            "",
        ]
        if requested_model:
            command.extend(["--model", requested_model])
        command.append(prompt)
        return command, None

    def _run_headless_prompt(
        self,
        prompt: str,
        model_name: Optional[str] = None,
    ) -> str:
        env = os.environ.copy()
        requested_model = model_name or self.model
        if self.cli_home:
            os.makedirs(self.cli_home, exist_ok=True)
            env["HOME"] = self.cli_home

        output_file: tempfile.NamedTemporaryFile[str] | None = None
        output_path: str | None = None
        if self.provider == "codex":
            output_file = tempfile.NamedTemporaryFile(
                "w+",
                encoding="utf-8",
                prefix="lawdigest-codex-summary-",
                suffix=".txt",
                delete=False,
            )
            output_path = output_file.name
            output_file.close()

        try:
            command, stdin_text = self._build_headless_command(prompt, requested_model, output_path)
            proc = subprocess.run(
                command,
                input=stdin_text,
                capture_output=True,
                text=True,
                cwd=self.cli_workdir,
                env=env,
                timeout=self.timeout_seconds,
            )
            output_text = ""
            if output_path:
                try:
                    output_text = Path(output_path).read_text(encoding="utf-8").strip()
                except FileNotFoundError:
                    output_text = ""
            if not output_text:
                output_text = (proc.stdout or "").strip()

            if proc.returncode != 0:
                stderr_text = (proc.stderr or "").strip()
                raise RuntimeError(f"{self.provider} CLI 실패: {stderr_text or output_text}")
            if not output_text:
                stderr_text = (proc.stderr or "").strip()
                raise RuntimeError(f"{self.provider} CLI 응답 본문이 비어 있습니다. {stderr_text}".strip())
            return output_text
        finally:
            if output_path:
                try:
                    Path(output_path).unlink(missing_ok=True)
                except Exception:
                    pass

    def _summarize_one(
        self, row: Dict[str, Any], model: Optional[str] = None
    ) -> Optional[StructuredBillSummary]:
        bill_id = row.get("bill_id")
        prompt = self._build_user_prompt(row)

        try:
            raw_text = self._run_headless_prompt(prompt, model_name=model)
            return self._extract_json_summary(raw_text)
        except Exception as exc:
            self.logger.error(f"[{self.provider} CLI 요약 실패] bill_id={bill_id}: {exc}")
            self.failed_bills.append({"bill_id": bill_id, "error": str(exc)})
            return None

    def AI_structured_summarize(
        self, df_bills: pd.DataFrame, model: Optional[str] = None
    ) -> pd.DataFrame:
        if df_bills is None or len(df_bills) == 0:
            return df_bills

        resolved_model = model or self.model

        for col in ("brief_summary", "gpt_summary"):
            if col not in df_bills.columns:
                df_bills[col] = None

        to_process = df_bills[
            df_bills["brief_summary"].isnull()
            | (df_bills["brief_summary"] == "")
            | df_bills["gpt_summary"].isnull()
            | (df_bills["gpt_summary"] == "")
        ]
        if len(to_process) == 0:
            return df_bills

        success = 0
        with trace_span(
            f"{self.provider}_cli_structured_summarize",
            input={"provider": self.provider, "model": resolved_model, "count": len(to_process)},
        ) as root_span:
            for idx, row in to_process.iterrows():
                bill_id = row.get("bill_id")
                with trace_generation(
                    root_span,
                    name=f"{self.provider}_cli_summarize_one",
                    model=resolved_model,
                    input={"bill_id": bill_id},
                ) as generation:
                    result = self._summarize_one(row.to_dict(), model=model)
                    if result is None:
                        continue
                    df_bills.loc[idx, "brief_summary"] = result.brief_summary
                    df_bills.loc[idx, "gpt_summary"] = result.gpt_summary
                    df_bills.loc[idx, "summary_tags"] = json.dumps(result.tags, ensure_ascii=False)
                    success += 1
                    if generation is not None:
                        generation.update(output={"bill_id": bill_id})

        print(f"[{self.provider} CLI 구조화 요약 완료] 성공={success}, 실패={len(to_process) - success}")
        return df_bills


class CodexCliSummarizer(GeminiCliSummarizer):
    def __init__(self):
        super().__init__(provider="codex")


class ClaudeCliSummarizer(GeminiCliSummarizer):
    def __init__(self):
        super().__init__(provider="claude")


def build_cli_summarizer(provider: str = "gemini") -> GeminiCliSummarizer:
    return GeminiCliSummarizer(provider=provider)
