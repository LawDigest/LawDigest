from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from lawdigest_ai.config import SUMMARY_STRUCTURED_MODEL, SUMMARY_STRUCTURED_FALLBACK_MODEL

import pandas as pd
from pydantic import BaseModel, Field

try:
    from pydantic_ai import Agent
except ImportError as exc:
    raise ImportError("pydantic-ai가 설치되어야 합니다.") from exc


class StructuredBillSummary(BaseModel):
    brief_summary: str = Field(description="법안 핵심을 한 문장으로 요약한 짧은 제목형 요약문")
    gpt_summary: str = Field(description="법안에서 달라지는 핵심 내용을 3~7개 항목으로 정리한 상세 요약문")
    tags: list[str] = Field(min_length=5, max_length=5, description="법안 주제를 나타내는 짧은 한국어 태그 5개")


class AISummarizer:
    def __init__(self):
        self.failed_bills: List[dict] = []
        self.logger = logging.getLogger(__name__)
        self.primary_model = SUMMARY_STRUCTURED_MODEL
        self.fallback_model = SUMMARY_STRUCTURED_FALLBACK_MODEL
        self.style_prompt = (
            "법률개정안 텍스트에서 달라지는 핵심 내용을 항목별로 정리하세요. "
            "각 항목은 이해하기 쉬운 공식 문체로 작성하고, 3~7개 항목을 권장합니다."
        )

    def _build_agent(self, model_name: str) -> Agent:
        return Agent(
            model=model_name,
            output_type=StructuredBillSummary,
            system_prompt="당신은 대한민국 법안 요약 전문가입니다. 반드시 structured output 스키마에 맞춰 응답하세요.",
        )

    def _build_user_prompt(self, row: Dict[str, Any]) -> str:
        intro = (
            f"[법안명] {row.get('bill_name') or '법안명 미상'}\n"
            f"[발의주체] {row.get('proposer_kind') or ''}\n"
            f"[발의자] {row.get('proposers') or '발의자 미상'}\n"
            f"[발의일] {row.get('proposeDate') or row.get('propose_date') or ''}\n"
            f"[단계] {row.get('stage') or ''}\n"
        )
        task = (
            f"{self.style_prompt}\n"
            "1) brief_summary: 한 문장 제목형 요약\n"
            "2) gpt_summary: 핵심 변경사항 상세 요약\n"
            "3) tags: 한국어 태그 정확히 5개 (중복 금지, 각 2~12자)\n"
        )
        return f"{intro}\n[원문 요약]\n{row.get('summary') or ''}\n\n{task}"

    def _summarize_one(self, row: Dict[str, Any], model: Optional[str] = None) -> Optional[StructuredBillSummary]:
        model_to_use = model or self.primary_model
        prompt = self._build_user_prompt(row)
        bill_id = row.get("bill_id")
        try:
            result = self._build_agent(model_to_use).run_sync(prompt)
            return result.output
        except Exception as e:
            self.logger.warning(f"[1차 실패] bill_id={bill_id}: {e}")
            if self.fallback_model and self.fallback_model != model_to_use:
                try:
                    result = self._build_agent(self.fallback_model).run_sync(prompt)
                    return result.output
                except Exception as e2:
                    self.logger.error(f"[2차 실패] bill_id={bill_id}: {e2}")
                    self.failed_bills.append({"bill_id": bill_id, "error": f"primary={e}; fallback={e2}"})
                    return None
            self.failed_bills.append({"bill_id": bill_id, "error": str(e)})
            return None

    def AI_structured_summarize(self, df_bills: pd.DataFrame, model: Optional[str] = None) -> pd.DataFrame:
        if df_bills is None or len(df_bills) == 0:
            return df_bills
        for col in ("brief_summary", "gpt_summary"):
            if col not in df_bills.columns:
                df_bills[col] = None

        to_process = df_bills[
            df_bills["brief_summary"].isnull() | (df_bills["brief_summary"] == "") |
            df_bills["gpt_summary"].isnull() | (df_bills["gpt_summary"] == "")
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

        print(f"[AI 구조화 요약 완료] 성공={success}, 실패={len(to_process) - success}")
        return df_bills
