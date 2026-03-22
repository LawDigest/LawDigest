from __future__ import annotations

import logging
import os
import json
from typing import Any, Dict, Optional

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

try:
    from pydantic_ai import Agent
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    raise ImportError(
        "pydantic-ai가 설치되어야 합니다. requirements.txt의 "
        "'pydantic-ai-slim[openai]'를 설치하세요."
    ) from exc


class StructuredBillSummary(BaseModel):
    brief_summary: str = Field(
        description="법안 핵심을 한 문장으로 요약한 짧은 제목형 요약문"
    )
    gpt_summary: str = Field(
        description="법안에서 달라지는 핵심 내용을 3~7개 항목으로 정리한 상세 요약문"
    )
    tags: list[str] = Field(
        min_length=5,
        max_length=5,
        description="법안 주제를 나타내는 짧은 한국어 태그 5개",
    )


class AISummarizer:
    def __init__(self):
        self.input_data = None
        self.output_data = None
        self.failed_bills = []
        self.logger = logging.getLogger(__name__)

        load_dotenv()
        self.primary_model = os.environ.get("SUMMARY_STRUCTURED_MODEL", "openai:gpt-4o-mini")
        self.fallback_model = os.environ.get("SUMMARY_STRUCTURED_FALLBACK_MODEL", "openai:gpt-4o-mini")

        self.style_prompt = (
            "법률개정안 텍스트에서 달라지는 핵심 내용을 항목별로 정리하세요. "
            "각 항목은 이해하기 쉬운 공식 문체로 작성하고, 3~7개 항목을 권장합니다."
        )

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
        proposer_kind = str(row.get("proposer_kind") or "").strip()
        proposer = str(row.get("proposers") or "발의자 미상")
        title = str(row.get("bill_name") or "법안명 미상")
        summary = str(row.get("summary") or "")
        stage = str(row.get("stage") or "")
        propose_date = str(row.get("proposeDate") or row.get("propose_date") or "")

        intro = (
            f"[법안명] {title}\n"
            f"[발의주체] {proposer_kind}\n"
            f"[발의자] {proposer}\n"
            f"[발의일] {propose_date}\n"
            f"[단계] {stage}\n"
        )
        task = (
            f"{self.style_prompt}\n"
            "1) brief_summary: 한 문장 제목형 요약\n"
            "2) gpt_summary: 핵심 변경사항 상세 요약\n"
            "3) tags: 한국어 태그 정확히 5개 (중복 금지, 각 2~12자)\n"
        )
        return f"{intro}\n[원문 요약]\n{summary}\n\n{task}"

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
