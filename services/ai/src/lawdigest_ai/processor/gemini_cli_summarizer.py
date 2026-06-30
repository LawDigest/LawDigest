from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import pandas as pd
from pydantic import ValidationError

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
from lawdigest_ai.observability import trace_generation, trace_span
from lawdigest_ai.processor.providers.openai_batch import (
    BatchStructuredSummary,
    _build_prompt_for_bill,
)
from lawdigest_ai.processor.category_taxonomy import category_label_to_code


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


StructuredBillSummary = BatchStructuredSummary


class GeminiCliSummarizer:
    def __init__(self, provider: str = "codex", fallback_provider: str | None = "codex"):
        config = _provider_config(provider)
        self.failed_bills: List[dict] = []
        self.usage_by_bill_id: Dict[str, dict[str, int]] = {}
        self.logger = logging.getLogger(__name__)
        self.provider = config.provider
        self.fallback_provider = fallback_provider if self.provider == "gemini" else None
        self.cli_bin = config.cli_bin
        self.model = config.model
        self.timeout_seconds = config.timeout_seconds
        self.approval_mode = config.approval_mode
        self.cli_home = config.cli_home
        self.cli_workdir = config.cli_workdir
        self.debug_log_path = os.getenv(f"{self.provider.upper()}_CLI_DEBUG_LOG_PATH")

    @staticmethod
    def _print_progress(message: str) -> None:
        print(f"[cli-summary] {message}", flush=True)

    def _build_user_prompt(self, row: Dict[str, Any]) -> str:
        api_prompt = _build_prompt_for_bill(row)
        schema = json.dumps(
            BatchStructuredSummary.model_json_schema(by_alias=True),
            ensure_ascii=False,
            sort_keys=True,
        )
        structured_contract = (
            "위 요청은 기존 API 기반 요약과 같은 프롬프트입니다.\n"
            "응답은 Pydantic structured output 계약과 같은 아래 JSON Schema를 반드시 준수하세요.\n"
            "JSON 객체 외의 설명, 마크다운, 코드펜스는 출력하지 마세요.\n"
            "키는 briefSummary, gptSummary, tags, category 네 개만 허용됩니다.\n"
            "brief_summary/gpt_summary 같은 snake_case 키를 사용하지 마세요.\n"
            f"{schema}"
        )
        return f"{api_prompt}\n\n{structured_contract}"

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
            return BatchStructuredSummary.model_validate(payload)
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
                "--skip-trust",
            ]
            if requested_model:
                command.extend(["--model", requested_model])
            return command, None

        if self.provider == "codex":
            command = [
                self.cli_bin,
                "exec",
                "--json",
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

    @staticmethod
    def _parse_codex_json_events(stdout_text: str) -> tuple[str | None, dict[str, int] | None]:
        last_message: str | None = None
        usage: dict[str, int] | None = None
        for line in stdout_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "item.completed":
                item = event.get("item")
                if isinstance(item, dict) and item.get("type") == "agent_message":
                    text = item.get("text")
                    if isinstance(text, str):
                        last_message = text
            elif event.get("type") == "turn.completed":
                raw_usage = event.get("usage")
                if isinstance(raw_usage, dict):
                    usage = {key: value for key, value in raw_usage.items() if isinstance(value, int)}
        return last_message, usage

    def _run_headless_prompt(
        self,
        prompt: str,
        model_name: Optional[str] = None,
    ) -> tuple[str, dict[str, int] | None]:
        env = os.environ.copy()
        requested_model = model_name or self.model
        temp_home: tempfile.TemporaryDirectory[str] | None = None
        if self.cli_home:
            os.makedirs(self.cli_home, exist_ok=True)
            env["HOME"] = self.cli_home
        if self.provider == "gemini":
            env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"
            env["TERM"] = "xterm-256color"
            env["COLORTERM"] = "truecolor"
            if not self.cli_home and env.get("GEMINI_API_KEY"):
                temp_home = tempfile.TemporaryDirectory(prefix="lawdigest-gemini-home-")
                gemini_home = Path(temp_home.name) / ".gemini"
                gemini_home.mkdir(parents=True, exist_ok=True)
                (gemini_home / "settings.json").write_text(
                    json.dumps(
                        {
                            "security": {"auth": {"selectedType": "gemini-api-key"}},
                            "output": {"format": "text"},
                            "general": {"defaultApprovalMode": self.approval_mode},
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                env["HOME"] = temp_home.name

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
            raw_stdout = (proc.stdout or "").strip()
            output_text = ""
            usage: dict[str, int] | None = None
            if output_path:
                try:
                    output_text = Path(output_path).read_text(encoding="utf-8").strip()
                except FileNotFoundError:
                    output_text = ""
            if not output_text:
                if self.provider == "codex":
                    output_text, usage = self._parse_codex_json_events(raw_stdout)
                    output_text = output_text or raw_stdout
                else:
                    output_text = raw_stdout
            elif self.provider == "codex":
                _, usage = self._parse_codex_json_events(raw_stdout)

            if proc.returncode != 0:
                stderr_text = (proc.stderr or "").strip()
                raise RuntimeError(f"{self.provider} CLI 실패: {stderr_text or output_text}")
            if not output_text:
                stderr_text = (proc.stderr or "").strip()
                raise RuntimeError(f"{self.provider} CLI 응답 본문이 비어 있습니다. {stderr_text}".strip())
            return output_text, usage
        finally:
            if output_path:
                try:
                    Path(output_path).unlink(missing_ok=True)
                except Exception:
                    pass
            if temp_home is not None:
                temp_home.cleanup()

    def _summarize_with_current_provider(
        self,
        row: Dict[str, Any],
        model: Optional[str] = None,
    ) -> StructuredBillSummary:
        prompt = self._build_user_prompt(row)
        raw_text, usage = self._run_headless_prompt(prompt, model_name=model)
        bill_id = row.get("bill_id")
        if bill_id is not None and usage is not None:
            self.usage_by_bill_id[str(bill_id)] = usage
        return self._extract_json_summary(raw_text)

    def _summarize_one(self, row: Dict[str, Any], model: Optional[str] = None) -> Optional[StructuredBillSummary]:
        bill_id = row.get("bill_id")
        primary_error: str | None = None

        try:
            return self._summarize_with_current_provider(row, model=model)
        except Exception as primary_exc:
            primary_error = str(primary_exc)
            self.logger.error(f"[{self.provider} CLI 요약 실패] bill_id={bill_id}: {primary_exc}")

        if self.fallback_provider:
            try:
                fallback = GeminiCliSummarizer(provider=self.fallback_provider, fallback_provider=None)
                return fallback._summarize_with_current_provider(row)
            except Exception as fallback_exc:
                self.logger.error(
                    f"[{self.provider}->{self.fallback_provider} CLI fallback 실패] "
                    f"bill_id={bill_id}: {fallback_exc}"
                )
                self.failed_bills.append(
                    {
                        "bill_id": bill_id,
                        "error": (
                            f"primary {self.provider} failed: {primary_error}; "
                            f"fallback {self.fallback_provider} failed: {fallback_exc}"
                        ),
                    }
                )
                return None

        self.failed_bills.append({"bill_id": bill_id, "error": primary_error or "unknown CLI failure"})
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
        self.usage_by_bill_id = {}
        with trace_span(
            f"{self.provider}_cli_structured_summarize",
            input={"provider": self.provider, "model": resolved_model, "count": len(to_process)},
        ) as root_span:
            total = len(to_process)
            for position, (idx, row) in enumerate(to_process.iterrows(), start=1):
                bill_id = row.get("bill_id")
                item_started_at = time.monotonic()
                self._print_progress(
                    f"{self.provider} item {position}/{total} start bill_id={bill_id}"
                )
                with trace_generation(
                    root_span,
                    name=f"{self.provider}_cli_summarize_one",
                    model=resolved_model,
                    input={"bill_id": bill_id},
                ) as generation:
                    result = self._summarize_one(row.to_dict(), model=model)
                    if result is None:
                        self._print_progress(
                            f"{self.provider} item {position}/{total} failed "
                            f"bill_id={bill_id} elapsed={time.monotonic() - item_started_at:.1f}s"
                        )
                        continue
                    df_bills.loc[idx, "brief_summary"] = result.brief_summary
                    df_bills.loc[idx, "gpt_summary"] = result.gpt_summary
                    df_bills.loc[idx, "summary_tags"] = json.dumps(result.tags, ensure_ascii=False)
                    df_bills.loc[idx, "category"] = category_label_to_code(result.category)
                    success += 1
                    usage = self.usage_by_bill_id.get(str(bill_id), {})
                    self._print_progress(
                        f"{self.provider} item {position}/{total} done "
                        f"bill_id={bill_id} elapsed={time.monotonic() - item_started_at:.1f}s "
                        f"input_tokens={usage.get('input_tokens', 0)} "
                        f"output_tokens={usage.get('output_tokens', 0)}"
                    )
                    if generation is not None:
                        generation.update(output={"bill_id": bill_id})

        print(f"[{self.provider} CLI 구조화 요약 완료] 성공={success}, 실패={len(to_process) - success}")
        return df_bills


class CodexCliSummarizer(GeminiCliSummarizer):
    def __init__(self):
        super().__init__(provider="codex", fallback_provider=None)


class ClaudeCliSummarizer(GeminiCliSummarizer):
    def __init__(self):
        super().__init__(provider="claude", fallback_provider=None)


def build_cli_summarizer(provider: str = "codex") -> GeminiCliSummarizer:
    return GeminiCliSummarizer(provider=provider)
