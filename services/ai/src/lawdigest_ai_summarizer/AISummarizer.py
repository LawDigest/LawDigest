from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

import pandas as pd
from dotenv import load_dotenv
from lawdigest_ai.processor.providers.openai_batch import BatchStructuredSummary, _build_prompt_for_bill

try:
    from pydantic_ai import Agent
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    raise ImportError(
        "pydantic-ai가 설치되어야 합니다. requirements.txt의 "
        "'pydantic-ai-slim[google,openai]>=0.7.0,<1.0.0'를 설치하세요."
    ) from exc


StructuredBillSummary = BatchStructuredSummary


class AISummarizer:
    def __init__(self):
        self.input_data = None
        self.output_data = None
        self.failed_bills = []
        self.logger = logging.getLogger(__name__)

        load_dotenv()
        self.primary_model = os.environ.get("SUMMARY_STRUCTURED_MODEL", "openai:gpt-4o-mini")
        self.fallback_model = os.environ.get("SUMMARY_STRUCTURED_FALLBACK_MODEL", "openai:gpt-4o-mini")

    def _build_agent(self, model_name: str) -> Agent:
        return Agent(
            model=model_name,
            output_type=StructuredBillSummary,
            system_prompt=(
                "당신은 대한민국 법안 요약 전문가입니다. "
                "반드시 structured output 스키마에 맞춰 응답하세요."
            ),
        )

    def _build_user_prompt(self, row: Dict[str, Any]) -> str:
        return _build_prompt_for_bill(row)

    def _summarize_one(self, row: Dict[str, Any], model: Optional[str] = None) -> Optional[StructuredBillSummary]:
        model_to_use = model or self.primary_model
        prompt = self._build_user_prompt(row)
        bill_info = {
            "bill_id": row.get("bill_id"),
            "bill_name": row.get("bill_name"),
        }

        try:
            agent = self._build_agent(model_to_use)
            result = agent.run_sync(prompt)
            return result.output
        except Exception as e:
            self.logger.warning(
                f"[1차 실패] structured summarize 실패: {type(e).__name__}: {e} "
                f"(bill_id={bill_info.get('bill_id')})"
            )

            if self.fallback_model and self.fallback_model != model_to_use:
                try:
                    fallback_agent = self._build_agent(self.fallback_model)
                    result = fallback_agent.run_sync(prompt)
                    return result.output
                except Exception as e2:
                    self.failed_bills.append(
                        {
                            "bill_id": bill_info.get("bill_id"),
                            "bill_name": bill_info.get("bill_name"),
                            "error": f"primary={e}; fallback={e2}",
                        }
                    )
                    self.logger.error(
                        f"[2차 실패] fallback summarize 실패: {type(e2).__name__}: {e2} "
                        f"(bill_id={bill_info.get('bill_id')})"
                    )
                    return None

            self.failed_bills.append(
                {
                    "bill_id": bill_info.get("bill_id"),
                    "bill_name": bill_info.get("bill_name"),
                    "error": str(e),
                }
            )
            return None

    def AI_structured_summarize(self, df_bills: pd.DataFrame, model: Optional[str] = None) -> pd.DataFrame:
        if df_bills is None or len(df_bills) == 0:
            return df_bills

        if "brief_summary" not in df_bills.columns:
            df_bills["brief_summary"] = None
        if "gpt_summary" not in df_bills.columns:
            df_bills["gpt_summary"] = None

        rows_to_process = df_bills[
            (df_bills["brief_summary"].isnull()) | (df_bills["brief_summary"] == "") |
            (df_bills["gpt_summary"].isnull()) | (df_bills["gpt_summary"] == "")
        ]

        total = len(rows_to_process)
        if total == 0:
            self.output_data = df_bills
            return df_bills

        print(f"\n[AI 구조화 요약 진행 중... total={total}]")
        success = 0
        for idx, row in rows_to_process.iterrows():
            result = self._summarize_one(row.to_dict(), model=model)
            if result is None:
                continue

            df_bills.loc[idx, "brief_summary"] = result.brief_summary
            df_bills.loc[idx, "gpt_summary"] = result.gpt_summary
            df_bills.loc[idx, "summary_tags"] = json.dumps(result.tags, ensure_ascii=False)
            success += 1

        print(f"[AI 구조화 요약 완료] 성공={success}, 실패={total - success}")
        self.output_data = df_bills
        return df_bills

    # 하위 호환: 기존 코드 경로에서 호출해도 1회 structured 요청으로 처리
    def AI_title_summarize(self, df_bills: pd.DataFrame, model: Optional[str] = None) -> pd.DataFrame:
        return self.AI_structured_summarize(df_bills, model=model)

    # 하위 호환: 기존 코드 경로에서 호출해도 1회 structured 요청으로 처리
    def AI_content_summarize(self, df_bills: pd.DataFrame, model: Optional[str] = None) -> pd.DataFrame:
        return self.AI_structured_summarize(df_bills, model=model)
