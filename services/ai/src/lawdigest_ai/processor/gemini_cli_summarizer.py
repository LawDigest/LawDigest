from __future__ import annotations

import json
import logging
import os
import queue
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from lawdigest_ai.config import (
    GEMINI_CLI_APPROVAL_MODE,
    GEMINI_CLI_BIN,
    GEMINI_CLI_HOME,
    GEMINI_CLI_MODEL,
    GEMINI_CLI_TIMEOUT_SECONDS,
    GEMINI_CLI_WORKDIR,
)


ACP_PROTOCOL_VERSION = 1
ACP_QUIET_MS = 0.3
ACP_SETTLE_TIMEOUT_SECONDS = 5.0
class StructuredBillSummary(BaseModel):
    brief_summary: str = Field(description="법안 핵심을 한 문장으로 요약한 짧은 제목형 요약문")
    gpt_summary: str = Field(description="법안에서 달라지는 핵심 내용을 3~7개 항목으로 정리한 상세 요약문")
    tags: list[str] = Field(min_length=5, max_length=5, description="법안 주제를 나타내는 짧은 한국어 태그 5개")


class GeminiCliSummarizer:
    def __init__(self):
        self.failed_bills: List[dict] = []
        self.logger = logging.getLogger(__name__)
        self.cli_bin = GEMINI_CLI_BIN
        self.model = GEMINI_CLI_MODEL
        self.timeout_seconds = GEMINI_CLI_TIMEOUT_SECONDS
        self.approval_mode = GEMINI_CLI_APPROVAL_MODE
        self.cli_home = GEMINI_CLI_HOME
        self.cli_workdir = GEMINI_CLI_WORKDIR
        self.debug_log_path = os.getenv("GEMINI_CLI_DEBUG_LOG_PATH")
        self.style_prompt = (
            "법률개정안 텍스트에서 달라지는 핵심 내용을 항목별로 정리하세요. "
            "각 항목은 이해하기 쉬운 공식 문체로 작성하고, 3~7개 항목을 권장합니다."
        )

    def _build_user_prompt(self, row: Dict[str, Any]) -> str:
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
            "- 반드시 다음 구조를 따르세요.\n"
            "  a. 첫 문장: '[발의자]이/가 발의한 [법안명]의 내용 및 목적은 다음과 같습니다:'\n"
            "  b. 본문: 3~5개의 번호 목록을 사용하세요. 각 항목은 반드시 '1. **[소제목]**: 설명' 형식으로 작성하세요.\n"
            "  c. 마지막 문단: '이 법안은 ...' 또는 '이번 개정안은 ...' 형식의 마무리 문장을 1개 추가하세요.\n"
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
    def _as_record(value: Any) -> Optional[Dict[str, Any]]:
        return value if isinstance(value, dict) else None

    @staticmethod
    def _as_string(value: Any, fallback: str = "") -> str:
        return value if isinstance(value, str) else fallback

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
        except json.JSONDecodeError as exc:
            json_object = self._extract_first_json_object(cleaned)
            if not json_object:
                raise ValueError(f"Gemini ACP 응답이 JSON이 아닙니다: {cleaned[:300]}") from exc
            payload = json.loads(json_object)
        try:
            return StructuredBillSummary.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Gemini ACP 구조화 응답 검증 실패: {exc}") from exc

    def _build_permission_outcome(self, params: Dict[str, Any]) -> Dict[str, Any]:
        options = params.get("options")
        if not isinstance(options, list):
            return {"outcome": "cancelled"}

        normalized: List[Dict[str, str]] = []
        for option in options:
            if not isinstance(option, dict):
                continue
            option_id = self._as_string(option.get("optionId"), "").strip()
            kind = self._as_string(option.get("kind"), "").strip()
            if option_id:
                normalized.append({"optionId": option_id, "kind": kind})

        preferred = ["allow_always", "allow_once"] if self.approval_mode == "yolo" else ["allow_once", "allow_always"]
        for kind in preferred:
            match = next((option for option in normalized if option["kind"] == kind), None)
            if match:
                return {"outcome": "selected", "optionId": match["optionId"]}
        return {"outcome": "cancelled"}

    def _run_acp_prompt(
        self,
        prompt: str,
        model_name: Optional[str] = None,
    ) -> str:
        env = os.environ.copy()
        requested_model = model_name or self.model
        if requested_model:
            env.setdefault("GEMINI_MODEL", requested_model)
        if self.cli_home:
            os.makedirs(os.path.join(self.cli_home, ".gemini"), exist_ok=True)
            env["HOME"] = self.cli_home

        proc = subprocess.Popen(
            [self.cli_bin, "--acp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.cli_workdir,
            env=env,
            bufsize=1,
        )
        if proc.stdin is None or proc.stdout is None or proc.stderr is None:
            proc.kill()
            raise RuntimeError("Gemini ACP stdio streams are unavailable")

        stdout_queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        stderr_chunks: List[str] = []
        message_chunks: List[str] = []
        session_id = ""
        request_seq = 0
        last_activity_at = time.time()
        write_lock = threading.Lock()

        def send_json(payload: Dict[str, Any]) -> None:
            line = json.dumps(payload, ensure_ascii=False)
            with write_lock:
                if proc.stdin is None or proc.stdin.closed:
                    raise RuntimeError("Gemini ACP stdin is closed")
                proc.stdin.write(line + "\n")
                proc.stdin.flush()

        def stdout_reader() -> None:
            nonlocal session_id, last_activity_at
            assert proc.stdout is not None
            for raw_line in proc.stdout:
                line = raw_line.strip()
                if not line:
                    continue
                last_activity_at = time.time()
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._append_debug_log("acp-line", line)

                method = self._as_string(payload.get("method"), "").strip()
                if method == "session/update":
                    params = self._as_record(payload.get("params")) or {}
                    if not session_id:
                        session_id = self._as_string(params.get("sessionId"), "").strip()
                    update = self._as_record(params.get("update")) or {}
                    update_type = self._as_string(update.get("sessionUpdate"), "").strip()
                    if update_type == "agent_message_chunk":
                        content = self._as_record(update.get("content")) or {}
                        if self._as_string(content.get("type"), "").strip() == "text":
                            chunk = self._as_string(content.get("text"), "")
                            if chunk:
                                message_chunks.append(chunk)
                                self._append_debug_log("message-chunk", chunk)
                    elif method and "id" in payload:
                        stdout_queue.put(payload)
                    continue

                if method and "id" in payload:
                    request_id = payload.get("id")
                    params = self._as_record(payload.get("params")) or {}
                    if method == "session/request_permission":
                        try:
                            send_json({
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": self._build_permission_outcome(params),
                            })
                        except Exception:
                            pass
                        continue

                    try:
                        send_json({
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Unsupported Gemini ACP client method: {method}",
                            },
                        })
                    except Exception:
                        pass
                    continue

                if "id" in payload:
                    stdout_queue.put(payload)

        def stderr_reader() -> None:
            assert proc.stderr is not None
            for chunk in proc.stderr:
                stderr_chunks.append(chunk)

        stdout_thread = threading.Thread(target=stdout_reader, daemon=True)
        stderr_thread = threading.Thread(target=stderr_reader, daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        def wait_for_response(request_id: str, timeout_seconds: float) -> Dict[str, Any]:
            deadline = time.time() + timeout_seconds
            while time.time() < deadline:
                if proc.poll() is not None and stdout_queue.empty():
                    break
                try:
                    payload = stdout_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                payload_id = self._as_string(payload.get("id"), "").strip()
                if payload_id != request_id:
                    continue
                error_payload = self._as_record(payload.get("error"))
                if error_payload:
                    message = self._as_string(error_payload.get("message"), "").strip() or json.dumps(error_payload, ensure_ascii=False)
                    raise RuntimeError(message)
                return self._as_record(payload.get("result")) or {}

            stderr_text = "".join(stderr_chunks).strip()
            raise RuntimeError(f"Gemini ACP 응답 대기 타임아웃: request_id={request_id} {stderr_text}".strip())

        def send_request(method: str, params: Dict[str, Any], timeout_seconds: Optional[float] = None) -> Dict[str, Any]:
            nonlocal request_seq
            request_seq += 1
            request_id = f"lawdigest-gemini-{request_seq}"
            send_json({
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            })
            return wait_for_response(request_id, timeout_seconds or self.timeout_seconds)

        try:
            send_request(
                "initialize",
                {
                    "protocolVersion": ACP_PROTOCOL_VERSION,
                    "clientCapabilities": {},
                    "clientInfo": {
                        "name": "lawdigest-ai",
                        "version": "0.1.0",
                    },
                },
            )

            created = send_request(
                "session/new",
                {
                    "cwd": self.cli_workdir,
                    "mcpServers": [],
                },
            )
            session_id = self._as_string(created.get("sessionId"), "").strip()
            if not session_id:
                raise RuntimeError("Gemini ACP did not return a session id")

            request_seq += 1
            send_json(
                {
                    "jsonrpc": "2.0",
                    "id": f"lawdigest-gemini-{request_seq}",
                    "method": "session/prompt",
                    "params": {
                        "sessionId": session_id,
                        "prompt": [
                            {
                                "type": "text",
                                "text": prompt,
                            }
                        ],
                    },
                }
            )

            deadline = time.time() + self.timeout_seconds
            while time.time() < deadline:
                output = "".join(message_chunks).strip()
                if output:
                    try:
                        self._extract_json_summary(output)
                        return output
                    except Exception:
                        pass
                if proc.poll() is not None:
                    break
                time.sleep(0.1)

            stderr_text = "".join(stderr_chunks).strip()
            partial = "".join(message_chunks).strip()
            if partial:
                raise RuntimeError(f"Gemini ACP 응답이 제한 시간 안에 완성되지 않았습니다. partial={partial[:500]}")
            raise RuntimeError(f"Gemini ACP 응답 본문이 비어 있습니다. {stderr_text}".strip())
        finally:
            try:
                if session_id and proc.stdin and not proc.stdin.closed:
                    send_json({
                        "jsonrpc": "2.0",
                        "method": "session/cancel",
                        "params": {
                            "sessionId": session_id,
                        },
                    })
            except Exception:
                pass
            try:
                if proc.stdin and not proc.stdin.closed:
                    proc.stdin.close()
            except Exception:
                pass
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    proc.wait(timeout=3)
                except Exception:
                    pass
            finally:
                try:
                    if proc.stdout and not proc.stdout.closed:
                        proc.stdout.close()
                except Exception:
                    pass
                try:
                    if proc.stderr and not proc.stderr.closed:
                        proc.stderr.close()
                except Exception:
                    pass
                stdout_thread.join(timeout=1)
                stderr_thread.join(timeout=1)

    def _summarize_one(
        self, row: Dict[str, Any], model: Optional[str] = None
    ) -> Optional[StructuredBillSummary]:
        bill_id = row.get("bill_id")
        prompt = self._build_user_prompt(row)

        try:
            raw_text = self._run_acp_prompt(prompt, model_name=model)
            return self._extract_json_summary(raw_text)
        except Exception as exc:
            self.logger.error(f"[Gemini CLI 요약 실패] bill_id={bill_id}: {exc}")
            self.failed_bills.append({"bill_id": bill_id, "error": str(exc)})
            return None

    def AI_structured_summarize(
        self, df_bills: pd.DataFrame, model: Optional[str] = None
    ) -> pd.DataFrame:
        if df_bills is None or len(df_bills) == 0:
            return df_bills

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
        for idx, row in to_process.iterrows():
            result = self._summarize_one(row.to_dict(), model=model)
            if result is None:
                continue
            df_bills.loc[idx, "brief_summary"] = result.brief_summary
            df_bills.loc[idx, "gpt_summary"] = result.gpt_summary
            df_bills.loc[idx, "summary_tags"] = json.dumps(result.tags, ensure_ascii=False)
            success += 1

        print(f"[Gemini CLI 구조화 요약 완료] 성공={success}, 실패={len(to_process) - success}")
        return df_bills
