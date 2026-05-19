from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from lawdigest_ai.config import SUMMARY_STRUCTURED_MODEL, SUMMARY_STRUCTURED_FALLBACK_MODEL
from lawdigest_ai.processor.providers.openai_batch import BatchStructuredSummary, _build_prompt_for_bill

import pandas as pd

try:
    from pydantic_ai import Agent
except ImportError as exc:
    raise ImportError("pydantic-ai가 설치되어야 합니다.") from exc


StructuredBillSummary = BatchStructuredSummary


class AISummarizer:
    def __init__(self):
        self.failed_bills: List[dict] = []
        self.logger = logging.getLogger(__name__)
        self.primary_model = SUMMARY_STRUCTURED_MODEL
        self.fallback_model = SUMMARY_STRUCTURED_FALLBACK_MODEL

    def _build_agent(self, model_name: str) -> Agent:
        return Agent(
            model=model_name,
            output_type=StructuredBillSummary,
            system_prompt="당신은 대한민국 법안 요약 전문가입니다. 반드시 structured output 스키마에 맞춰 응답하세요.",
        )

    def _build_user_prompt(self, row: Dict[str, Any]) -> str:
        return _build_prompt_for_bill(row)

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
