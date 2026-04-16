from __future__ import annotations

import argparse
import json
from pathlib import Path

from lawdigest_ai.processor.instant_summarizer import summarize_single_bill_with_gemini_cli


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini CLI로 단일 법안을 요약하고 JSON 파일로 저장합니다.")
    parser.add_argument("--input", required=True, help="입력 법안 JSON 파일 경로")
    parser.add_argument("--output", required=True, help="출력 결과 JSON 파일 경로")
    args = parser.parse_args()

    input_path = Path(args.input)
    bill_data = json.loads(input_path.read_text(encoding="utf-8"))
    result = summarize_single_bill_with_gemini_cli(bill_data, output_path=args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
