# PDF 파서 개발 가이드

> 대상 독자: 에이전트 또는 개발자가 새 여론조사 기관 파서를 처음부터 개발할 때 참고

## 핵심 원칙

**각 여론조사 기관마다 반드시 새 파서 클래스를 작성한다.**

기존 파서를 다른 기관에 재사용하면 포맷 차이로 인한 파싱 오류를 놓치기 쉽다.\
기존 파서는 코드 구조 참고용으로만 활용하고, 실제 로직은 해당 기관 PDF를 직접 분석하여 작성한다.
동일 포맷이 이미 검증된 경우에는 새 클래스를 만들지 말고 `pollster_names` 별칭만 추가한다.

## 개발 프로세스

```text
1. 스크리닝 실행  →  2. 포맷 분석  →  3. 파서 작성  →  4. 픽스처 검증  →  5. PR 제출
```

### 1단계: 스크리닝 실행

```bash
cd services/data

# 특정 기관 PDF 스크리닝 (JSON + human 출력)
python scripts/dev/diagnose_pdf.py \
  --pdf "결과분석_한길리서치1019.pdf" \
  --pollster "(주)한길리서치" \
  --human --dump-text

# 결과 JSON 확인
cat output/polls/screening/(주)한길리서치/결과분석_한길리서치1019.json
```

스크리닝 결과 JSON의 핵심 필드:

| 필드                                                    | 설명          | 파서 개발에서의 의미           |
| ----------------------------------------------------- | ----------- | --------------------- |
| `question_block_patterns.detected_markers`            | 질문 시작 마커 목록 | 질문 블록 분리 정규식 기준       |
| `total_row_markers.detected_markers`                  | 전체/합계 행 마커  | overall 비율 행 탐지 기준    |
| `table_structure.header_row_analysis.meta_cols_count` | meta 컬럼 수   | 선택지 컬럼 시작 인덱스         |
| `table_structure.ratio_data_location`                 | 비율 데이터 위치   | 셀 직접 읽기 vs 텍스트 파싱 분기  |
| `table_structure.ratio_cell_bundled`                  | 비율 뭉침 여부    | 셀 내 공백 분리 추가 파싱 필요 여부 |
| `page_continuity.multi_page_questions_detected`       | 페이지 연속성     | 멀티페이지 merge 로직 필요 여부  |
| `format_profile.key_challenges`                       | 주요 도전 과제 요약 | 파서 작성 전 확인할 체크리스트     |
| `text_samples.first_pages_text`                       | 실제 텍스트 샘플   | 정규식 패턴 검증에 직접 활용      |
| `text_samples.table_previews`                         | 테이블 첫 5행    | 헤더 구조 및 셀 레이아웃 파악     |

### 2단계: 포맷 분석

스크리닝 결과에서 다음을 확인한다.

#### 2-1. 비율 위치 판별 (가장 중요)

| `ratio_data_location` | 의미             | 파싱 접근법                     |
| --------------------- | -------------- | -------------------------- |
| `table_cell`          | 각 셀에 개별 숫자     | 테이블 행에서 float 변환           |
| `text_bundled`        | 텍스트에 공백으로 뭉쳐있음 | 정규식으로 숫자 시퀀스 추출            |
| `mixed`               | 혼재             | 전체 행은 텍스트, 크로스탭은 셀 — 분기 처리 |
| `mixed (비율 뭉침 감지)`    | 셀에 뭉침          | 셀을 공백으로 split 후 float 변환   |

#### 2-2. `--dump-text` 로 실제 구조 확인

```bash
python scripts/dev/diagnose_pdf.py \
  --pdf "파일명.pdf" --pollster "기관명" \
  --human --dump-text --pages 10
```

`[8] 텍스트 샘플`과 테이블 샘플을 보면서:

* 질문 마커가 실제로 어떤 형태인지 (`[표1]`, `Q1.`, `문1)` 등)

* 전체 행이 정확히 어떤 문자열인지

* 테이블 헤더의 정확한 컬럼 수와 선택지 위치

### 3단계: 파서 작성

#### 3-1. 파일 위치

```text
services/data/src/lawdigest_data/polls/parser.py
```

모든 파서는 이 단일 파일 안에 private class로 작성한다.

#### 3-2. 클래스 구조

```python
class _XxxParser(_TableFormatParser):  # 코드 구조 참고용 베이스
    """기관명 파서.

    포맷 특성:
      - 질문 마커: 문N)
      - 전체 행 마커: 합계
      - 비율 위치: mixed (셀 내 뭉침)
      - meta 컬럼: 2개
    """

    # ── 정규식 패턴 ─────────────────────────────────────────────
    _Q_RE   = re.compile(r"문\s*(\d+)\)\s*(.+?)(?=문\s*\d+\)|$)", re.DOTALL)
    _TOT_RE = re.compile(r"^합계\s", re.MULTILINE)

    def parse(self, pages_data: list) -> list[QuestionResult]:
        ...
```

#### 3-3. 비율 뭉침 처리 패턴

`ratio_cell_bundled = True`인 경우 전체 행 셀이 `"42.6 12.5 55.1 39.0 ..."` 형태다.

```python
# 뭉친 비율 셀 분리
def _split_bundled_ratios(cell: str) -> list[float]:
    parts = cell.split()
    result = []
    for p in parts:
        try:
            v = float(p.replace(",", ""))
            if 0.0 <= v <= 100.0:
                result.append(v)
        except ValueError:
            break  # 숫자가 끊기는 지점에서 종료
    return result
```

#### 3-4. 멀티페이지 merge 패턴

`page_continuity.multi_page_questions_detected = True`인 경우:

```python
# 같은 질문이 여러 페이지에 걸친 경우 merge
def _merge_pages(pages_data):
    merged = []
    for outside_text, tables, full_text in pages_data:
        if merged and _is_continuation(tables, merged[-1]["tables"]):
            merged[-1]["tables"].extend(tables)
            merged[-1]["text"] += "\n" + outside_text
        else:
            merged.append({"text": outside_text, "tables": tables})
    return merged
```

#### 3-5. 레지스트리 등록

`config/parser_registry.json`에 추가:

```json
"xxx_format": {
  "class": "_XxxParser",
  "description": "기관명 파서 — 포맷 특성 한 줄 요약",
  "pollster_names": ["기관명 키워드"]
}
```

### 4단계: 픽스처 검증

```bash
# generate_parser_fixtures.py의 TARGETS에 추가 후 실행
python scripts/dev/generate_parser_fixtures.py --pollster "기관명 키워드" --force

# 테스트 실행
python -m pytest tests/polls/ -x -q
```

픽스처 파일: `tests/polls/fixtures/{pdf_stem}.json`

검증 항목:

* `question_count > 0`

* 각 질문의 `overall_percentages` 합계가 75~115% 범위

* `response_options` 개수 = `overall_percentages` 개수

### 5단계: PR 제출

```bash
# 린트
ruff check src/lawdigest_data/polls/parser.py

# 커밋
git add src/lawdigest_data/polls/parser.py config/parser_registry.json tests/polls/fixtures/
git commit -m "feat: {기관명} 파서 추가"

# PR 작성
gh pr create --title "{기관명} 파서 개발" --body-file /tmp/pr_body.md
```

## 파서 선택 로직

`PollResultParser.parse_pdf(pdf_path, pollster_hint=None)` 호출 시:

1. `pollster_hint`에서 `parser_registry.json`의 `pollster_names` 키워드 매칭

2. 매칭되면 해당 파서 클래스 사용

3. 미매칭 시 `UnknownPollsterError`를 발생시킨다

```python
# 사용 예
parser = PollResultParser(registry_path=Path("config/parser_registry.json"))
results = parser.parse_pdf(pdf_path, pollster_hint="(주)한길리서치")
```

## 기존 파서 포맷 레퍼런스

새 파서 작성 시 유사한 포맷의 기존 파서 코드를 구조 참고용으로 활용한다.

| 파서 클래스                  | 질문 마커          | 전체 행 마커  | 비율 위치        | 특이사항               |
| ----------------------- | -------------- | -------- | ------------ | ------------------ |
| `_TableFormatParser`    | `문N)`, `N번)`   | `▣ 전체 ▣` | table_cell   | 기본 크로스탭 구조         |
| `_TextFormatParser`     | `N번)`          | 텍스트 내    | text_bundled | 텍스트 섹션 기반          |
| `_RealMeterParser`      | `N.`           | `전체`     | mixed        | 헤더 선택지 + 텍스트 비율    |
| `_EmbrainPublicParser`  | `[표N]`         | `■ 전체 ■` | table_cell   | col4+ 선택지          |
| `_KoreanResearchParser` | `[표N]`, `[문N]` | `▣ 전체 ▣` | table_cell   | 페이지 분할 merge       |
| `_SignalPulseParser`    | `[표N]`, `[QN]` | `▣ 전체 ▣` | table_cell   | 두 버전 분기            |
| `_FlowerResearchParser` | (cid 인코딩)      | `전체`     | table_cell   | GID→Unicode 역맵핑 필요 |

## 스크리닝 도구 레퍼런스

```text
scripts/dev/
├── diagnose_pdf.py           # CLI 엔트리포인트
└── screening/
    ├── models.py             # 출력 스키마 (ScreeningResult, FormatProfile 등)
    ├── pdf_analyzer.py       # PDF 기본 분석 (PdfAnalyzer)
    ├── pattern_detector.py   # 5종 패턴 탐지 (PatternDetector)
    ├── parser_tester.py      # 기존 파서 시도 (ParserTester)
    ├── format_profiler.py    # 포맷 프로파일 생성 (FormatProfiler)
    ├── profiler.py           # 기관별 공통 패턴 집약 (Profiler)
    └── output.py             # JSON/human 출력 (ScreeningOutput)
```

### CLI 옵션

| 옵션                    | 설명                      |
| --------------------- | ----------------------- |
| `--pdf`, `--pollster` | 단일 PDF 지정               |
| `--human`             | 터미널 출력 (기본: JSON 파일 저장) |
| `--dump-text`         | 텍스트/테이블 상세 포함           |
| `--pages N`           | 상세 분석 페이지 수 (기본: 5)     |
| `--stdout`            | JSON을 stdout으로 출력       |
| `--profile`           | 기관별 공통 패턴 프로파일 생성       |

## 알려진 포맷 패턴 카탈로그

스크리닝 결과 기준 미개발 기관 포맷 요약:

| 기관                | 질문마커   | 전체행   | 비율위치         | 주요 도전           |
| ----------------- | ------ | ----- | ------------ | --------------- |
| 케이스탯리서치 (KBS)     | `N)`   | `전 체` | text_bundled | 멀티페이지 merge     |
| 케이스탯리서치 (12.31)   | 탐지 안 됨 | `계`   | text_bundled | 질문 마커 수동 확인     |
| 윈지코리아컨설팅 (250915) | `QN.`  | `전 체` | mixed+뭉침     | 비율 셀 분리 + 멀티페이지 |
| 윈지코리아컨설팅 (260305) | `QN.`  | `전체`  | mixed+뭉침     | 비율 셀 분리         |
| 넥스트리서치            | `N.`   | `계`   | mixed+뭉침     | 비율 셀 분리         |
| 에스티아이             | `QN.`  | `계`   | mixed+뭉침     | 비율 셀 분리 + 멀티페이지 |
| 입소스               | `문N.`  | `전 체` | text_bundled | 멀티페이지 merge     |
| 한길리서치             | `문N)`  | `합계`  | mixed+뭉침     | 비율 셀 분리         |

> 상세 스크리닝 JSON: `output/polls/screening/{기관명}/`
