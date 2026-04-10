# PDF 파서 개발 가이드

> 대상 독자: 에이전트 또는 개발자가 새 여론조사 기관 파서를 처음부터 개발할 때 참고

## 핵심 원칙

**각 여론조사 기관마다 반드시 새 파서 클래스를 작성한다.**

기존 파서를 다른 기관에 재사용하면 포맷 차이로 인한 파싱 오류를 놓치기 쉽다.
기존 파서는 코드 구조 참고용으로만 활용하고, 실제 로직은 해당 기관 PDF를 직접 분석하여 작성한다.
동일 포맷이 이미 검증된 경우에는 새 클래스를 만들지 말고 `pollster_names` 별칭만 추가한다.

---

## 개발 프로세스

```text
0. (필요 시) 목록 수집 / PDF 다운로드
1. 스크리닝 실행  →  2. 포맷 분석  →  3. 파서 작성
4. 단일 PDF 테스트  →  4.5. 디버깅  →  5. 픽스처 검증  →  6. PR 제출
```

모든 명령은 `cd services/data` 후 실행한다.

---

## 도구 레퍼런스

### 도구 목록 요약

| 도구 | 위치 | 용도 |
|------|------|------|
| `collect_all_regions_poll_list.py` | `scripts/polls/` | NESDC 전국 여론조사 목록 수집 |
| `collect_poll_list.py` | `scripts/polls/` | 특정 타겟(지역+선거) 목록 수집 |
| `download_pdfs.py` | `scripts/polls/` | poll_targets.json 기준 PDF 다운로드 |
| `diagnose_pdf.py` | `scripts/dev/` | 단일 PDF 포맷 스크리닝 (파서 개발 핵심 도구) |
| `parse_all.py` | `scripts/polls/` | 다운로드된 PDF 전체 파싱 및 결과 저장 |
| `probe_parsers.py` | `scripts/polls/` | 파서 동작 전체 검증 리포트 |
| `analyze_parser_coverage.py` | `scripts/polls/` | 기관별 파서 커버리지 분석 |
| `generate_parser_fixtures.py` | `scripts/dev/` | 파서 테스트 픽스처 생성 |
| `check_pdfs.py` | `scripts/polls/` | PDF 파일 상태 점검 |

---

### `collect_all_regions_poll_list.py` — 전국 목록 수집

NESDC에서 제9회 전국동시지방선거(VT026) 여론조사 목록 전체를 수집한다.
인자 없이 실행하며, 10페이지마다 체크포인트를 저장해 중단 후 재시작이 가능하다.

```bash
python scripts/polls/collect_all_regions_poll_list.py
```

**출력 파일:**
- `output/polls/lists/all_regions_9th.json` — 전체 레코드 (JSON)
- `output/polls/lists/all_regions_9th.csv` — 전체 레코드 (CSV)
- `output/polls/lists/all_regions_9th.ckpt` — 재시작용 체크포인트

**레코드 필드:**

| 필드 | 설명 |
|------|------|
| `pollster` | 조사기관명 |
| `province` | 지역 (서울특별시, 경기도 등) |
| `ntt_id` | NESDC 게시글 ID (PDF 다운로드에 필요) |
| `detail_url` | 상세 페이지 URL |
| `registered_date` | 등록일 |
| `title_region` | 조사 제목/지역 요약 |

> **주의:** `pdf_url` 필드는 이 스크립트로는 수집되지 않는다. PDF는 상세 페이지를 직접 크롤링하거나 `download_pdfs.py`를 사용한다.

**파서 개발 시 활용법:**
```python
import json
with open("output/polls/lists/all_regions_9th.json") as f:
    polls = json.load(f)

# 특정 기관 목록 확인
gallup = [p for p in polls if "갤럽" in p.get("pollster", "")]
print(f"{len(gallup)}건, ntt_id 예시: {gallup[0]['ntt_id']}")
```

---

### `collect_poll_list.py` — 타겟별 목록 수집

`poll_targets.json`에 정의된 특정 타겟(지역+선거 조합)의 여론조사 목록을 수집한다.

```bash
# 기본 (poll_targets.json의 첫 번째 타겟)
python scripts/polls/collect_poll_list.py

# 특정 타겟 지정
python scripts/polls/collect_poll_list.py --target gyeonggi_governor_9th
python scripts/polls/collect_poll_list.py --target seoul_mayor_9th
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `--target SLUG` | `poll_targets.json`의 slug. 미지정 시 첫 번째 타겟 사용 |

**출력:** `output/polls/checks/{slug}.json` — PDF URL 포함 상세 목록

**`poll_targets.json` 구조 (config/poll_targets.json):**
```json
{
  "targets": [
    {
      "slug": "gyeonggi_governor_9th",
      "region_key": "gyeonggi",
      "election_key": "local_9th_governor",
      "ignored_analysis_filenames": ["무관한파일.pdf"]
    }
  ]
}
```

새 지역을 추가하려면 `regions`, `elections`, `targets` 세 섹션에 각각 항목을 추가한다.

---

### `download_pdfs.py` — PDF 다운로드

`collect_poll_list.py`가 생성한 `output/polls/checks/{slug}.json`에서 PDF URL을 읽어 다운로드한다.

```bash
# 기본 (첫 번째 타겟)
python scripts/polls/download_pdfs.py

# 특정 타겟
python scripts/polls/download_pdfs.py --target gyeonggi_governor_9th
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `--target SLUG` | 타겟 slug. 미지정 시 첫 번째 타겟 사용 |

**출력:** `output/pdfs/{선거명}/{지역명}/{파일명}.pdf`

> **주의:** `collect_poll_list.py`로 목록을 먼저 수집해야 PDF URL이 존재한다.

**파서 개발 시 특정 기관 PDF 수동 다운로드:**

전국 목록에서 `ntt_id`를 가져온 뒤 NESDC 상세 페이지를 직접 크롤링한다:
```python
import requests
from bs4 import BeautifulSoup

ntt_id = "18052"
url = f"https://www.nesdc.go.kr/portal/bbs/B0000005/view.do?nttId={ntt_id}&menuNo=200467"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(r.text, "html.parser")
# PDF 파일 링크 탐색 — 기관별로 HTML 구조가 다를 수 있음
```

---

### `diagnose_pdf.py` — PDF 포맷 스크리닝 ⭐ 가장 중요한 도구

파서 개발의 핵심 도구. 단일 PDF를 분석해 질문 마커, 전체 행, 테이블 구조, 비율 위치 등을 자동으로 탐지한다.

```bash
# 기본: JSON 저장 + 터미널 출력
python scripts/dev/diagnose_pdf.py \
  --pdf "결과분석_한길리서치1019.pdf" \
  --pollster "(주)한길리서치" \
  --human --dump-text

# 텍스트/테이블 상세 포함, 10페이지까지 분석
python scripts/dev/diagnose_pdf.py \
  --pdf "파일명.pdf" --pollster "기관명" \
  --human --dump-text --pages 10

# 파서 클래스 뼈대(scaffold) 자동 생성
python scripts/dev/diagnose_pdf.py \
  --pdf "파일명.pdf" --pollster "기관명" \
  --human --scaffold

# PDF가 기본 경로가 아닌 경우 직접 지정
python scripts/dev/diagnose_pdf.py \
  --pdf "파일명.pdf" --pollster "기관명" \
  --pdf-dir "output/polls/screening_dl/기관명/pdfs" \
  --human --dump-text
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `--pdf FILE` | PDF 파일명 (경로 제외, 파일명만) |
| `--pollster NAME` | 기관명 (`--pdf`와 함께 사용) |
| `--human` | 터미널 출력 (기본: JSON 파일만 저장) |
| `--dump-text` | 텍스트/테이블 상세 내용 포함 |
| `--pages N` | 상세 분석 페이지 수 (기본: 5) |
| `--stdout` | JSON을 stdout으로 출력 |
| `--profile` | 기관별 공통 패턴 프로파일 생성 |
| `--scaffold` | FormatProfile 기반 파서 클래스 뼈대 생성 |
| `--pdf-dir PATH` | PDF 디렉토리 경로 직접 지정 |

**출력:** `output/polls/screening/{기관명}/{파일명}.json`

**스크리닝 결과 JSON 핵심 필드:**

| 필드 | 설명 | 파서 개발에서의 의미 |
|------|------|---------------------|
| `question_block_patterns.detected_markers` | 질문 시작 마커 목록 | 질문 블록 분리 정규식 기준 |
| `total_row_markers.detected_markers` | 전체/합계 행 마커 | overall 비율 행 탐지 기준 |
| `table_structure.header_row_analysis.meta_cols_count` | meta 컬럼 수 | 선택지 컬럼 시작 인덱스 |
| `table_structure.ratio_data_location` | 비율 데이터 위치 | 셀 직접 읽기 vs 텍스트 파싱 분기 |
| `table_structure.ratio_cell_bundled` | 비율 뭉침 여부 | 셀 내 공백 분리 추가 파싱 필요 여부 |
| `page_continuity.multi_page_questions_detected` | 페이지 연속성 | 멀티페이지 merge 로직 필요 여부 |
| `format_profile.key_challenges` | 주요 도전 과제 요약 | 파서 작성 전 확인할 체크리스트 |
| `text_samples.first_pages_text` | 실제 텍스트 샘플 | 정규식 패턴 검증에 직접 활용 |
| `text_samples.table_previews` | 테이블 첫 5행 | 헤더 구조 및 셀 레이아웃 파악 |

---

### `probe_parsers.py` — 파서 전체 검증

다운로드된 PDF 전체에 파서를 실행하고 성공/실패 통계를 출력한다. 파서 구현 후 품질 검증에 사용한다.

```bash
# 기본 (첫 번째 타겟)
python scripts/polls/probe_parsers.py

# 특정 타겟
python scripts/polls/probe_parsers.py --target gyeonggi_governor_9th

# DEBUG 로그 포함 (파싱 실패 원인 추적)
python scripts/polls/probe_parsers.py --target gyeonggi_governor_9th --verbose
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `--target SLUG` | 검증할 타겟 slug |
| `--verbose` | parser.py의 DEBUG 로그 출력 (SKIP 원인 포함) |

> **파서 개발 팁:** `--verbose`를 사용하면 각 페이지에서 왜 파싱이 스킵됐는지 `[XXX] p5 SKIP: 전체 행 미발견` 형태로 즉시 확인 가능하다.

---

### `analyze_parser_coverage.py` — 커버리지 분석

전국 목록(`all_regions_9th.json`)과 `parser_registry.json`을 대조해 기관별/지역별 파서 커버리지를 집계한다.

```bash
python scripts/polls/analyze_parser_coverage.py
```

인자 없이 실행. 결과를 터미널에 출력하고 `output/polls/coverage/coverage_report.json`에 저장한다.

**커버리지 분류:**
- `supported` — `parser_registry.json`에 매핑된 기관
- `unparseable` — 구조적 한계로 파싱 불가 (`unparseable` 섹션 등록된 기관)
- `uncovered` — 파서 미개발 기관

---

### `parse_all.py` — 전체 파싱 실행

다운로드된 PDF 전체를 파싱해 결과를 JSON으로 저장한다.

```bash
# 특정 타겟 전체 파싱
python scripts/polls/parse_all.py --target gyeonggi_governor_9th

# 특정 기관만 파싱
python scripts/polls/parse_all.py --target gyeonggi_governor_9th --pollster "한길리서치"

# 이미 파싱된 것도 덮어쓰기
python scripts/polls/parse_all.py --target gyeonggi_governor_9th --force

# PDF 디렉토리 직접 지정
python scripts/polls/parse_all.py --pdf-dir "output/polls/screening_dl/기관명/pdfs"
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `--target SLUG` | 파싱할 타겟 |
| `--pollster NAME` | 특정 기관만 파싱 (부분 문자열 매칭) |
| `--force` | 기존 결과 덮어쓰기 |
| `--pdf-dir PATH` | PDF 디렉토리 직접 지정 |

---

### `generate_parser_fixtures.py` — 픽스처 생성

파서 테스트에 사용할 픽스처 JSON을 생성한다. `tests/polls/fixtures/`에 저장된다.

```bash
# 특정 기관 픽스처 생성
python scripts/dev/generate_parser_fixtures.py --pollster "한길리서치"

# 기존 픽스처 덮어쓰기
python scripts/dev/generate_parser_fixtures.py --pollster "한길리서치" --force
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `--pollster NAME` | 기관명 키워드 (부분 일치) |
| `--force` | 기존 픽스처 덮어쓰기 |

**픽스처 파일 위치:** `tests/polls/fixtures/{pdf_stem}.json`

---

### `check_pdfs.py` — PDF 존재 여부 확인

다운로드가 완료된 PDF 파일의 상태(파일 존재 여부, 손상 여부 등)를 점검한다.
`download_pdfs.py` 실행 후 누락된 파일이 없는지 확인할 때 사용한다.

```bash
# 기본 (첫 번째 타겟)
python scripts/polls/check_pdfs.py

# 특정 타겟
python scripts/polls/check_pdfs.py --target gyeonggi_governor_9th
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `--target SLUG` | 확인할 타겟 slug. 미지정 시 첫 번째 타겟 사용 |

---

## 파서 개발 단계별 절차

### 0단계: 대상 PDF 확보

```bash
# 전국 목록에서 기관 확인
python3 -c "
import json
polls = json.load(open('output/polls/lists/all_regions_9th.json'))
target = [p for p in polls if '갤럽' in p.get('pollster', '')]
print(f'{len(target)}건')
for p in target[:3]:
    print(p['ntt_id'], p['detail_url'])
"

# poll_targets.json에 새 타겟 추가 후 목록 수집 + 다운로드
python scripts/polls/collect_poll_list.py --target new_target_slug
python scripts/polls/download_pdfs.py --target new_target_slug
```

### 1단계: 스크리닝 실행

```bash
# 다운로드된 PDF 스크리닝 (--pdf-dir로 경로 지정)
python scripts/dev/diagnose_pdf.py \
  --pdf "파일명.pdf" \
  --pollster "기관명" \
  --pdf-dir "output/pdfs/제9회전국동시지방선거/지역명" \
  --human --dump-text

# 스크리닝 결과 JSON 열람
cat "output/polls/screening/기관명/파일명.json" | python3 -m json.tool | head -80
```

### 2단계: 포맷 분석

스크리닝 결과에서 다음을 확인한다.

#### 2-1. 비율 위치 판별 (가장 중요)

| `ratio_data_location` | 의미 | 파싱 접근법 |
|-----------------------|------|------------|
| `table_cell` | 각 셀에 개별 숫자 | 테이블 행에서 float 변환 |
| `text_bundled` | 텍스트에 공백으로 뭉쳐있음 | 정규식으로 숫자 시퀀스 추출 |
| `mixed` | 혼재 | 전체 행은 텍스트, 크로스탭은 셀 — 분기 처리 |
| `mixed (비율 뭉침 감지)` | 셀에 뭉침 | 셀을 공백으로 split 후 float 변환 |

#### 2-2. `--dump-text`로 실제 구조 확인

`[8] 텍스트 샘플`과 테이블 샘플을 보면서:
- 질문 마커가 실제로 어떤 형태인지 (`[표1]`, `Q1.`, `문1)` 등)
- 전체 행이 정확히 어떤 문자열인지
- 테이블 헤더의 정확한 컬럼 수와 선택지 위치
- `%` 기호 포함 여부 (포함 시 `extract_percentages_from_cells()` 사용 불가)

### 3단계: 파서 작성

#### 3-1. 파일 위치

```text
services/data/src/lawdigest_data/polls/parser.py
```

모든 파서는 이 단일 파일 안에 private class로 작성한다.

#### 3-2. 클래스 구조

```python
class _XxxParser:
    """기관명 파서.

    포맷 특성:
      - 질문 마커: 문N)  (outside_text 기반)
      - 전체 행 마커: 합계  (row[0])
      - 비율 위치: table_cell
      - meta 컬럼: 4개 (구분, None, 완료사례수, 가중사례수)
    """

    PARSER_KEY = "_XxxParser"
    TOTAL_MARKERS = frozenset({"합계", "전체"})
    SUMMARY_PATS = DEFAULT_SUMMARY_PATTERNS + (re.compile(r"^계$"),)
    _META_PAGE_MARKERS = frozenset({"조사개요", "조사방법"})
    _Q_TITLE_RE = re.compile(r"^\d+[.\)]\s*(.+?)(?:\n|$)", re.MULTILINE)

    def parse(self, pages_data: List[PageData]) -> List[QuestionResult]:
        results: List[QuestionResult] = []

        for pg_idx, (outside_text, page_tables, _full_text) in enumerate(pages_data):
            pg = pg_idx + 1

            if any(m in outside_text for m in self._META_PAGE_MARKERS):
                _logger.debug("[XXX] p%d SKIP: 메타 페이지", pg)
                continue
            # ... 이하 단계별 SKIP 체크 + debug 로그
        return results
```

#### 3-3. 비율 뭉침 처리 패턴

`ratio_cell_bundled = True`인 경우 전체 행 셀이 `"42.6 12.5 55.1 39.0 ..."` 형태다.

```python
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

#### 3-4. `%` 기호 포함 셀 처리

`extract_percentages_from_cells()`는 순수 숫자 문자열만 처리한다. `'47.0%'` 형태는 **빈 리스트를 반환**한다.
이 경우 파서 내에 전용 메서드를 추가한다:

```python
@staticmethod
def _extract_pct_cells(row: List, start_col: int, end_col=None) -> List[float]:
    result = []
    for cell in row[start_col:end_col]:
        text = str(cell or "").strip().rstrip("%")
        try:
            v = float(text)
        except ValueError:
            continue
        if 0.0 <= v <= 100.0:
            result.append(v)
    return result
```

#### 3-5. 멀티페이지 merge 패턴

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

#### 3-6. 레지스트리 등록

`config/parser_registry.json`에 추가 (version도 올린다):

```json
"xxx_format": {
  "class": "_XxxParser",
  "description": "기관명 파서 — 포맷 특성 한 줄 요약",
  "pollster_names": ["기관명 키워드", "(주)기관명"]
}
```

### 4단계: 단일 PDF 테스트

```python
import sys, logging
from pathlib import Path

# DEBUG 로그 활성화 (parser.py만)
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
logging.getLogger("lawdigest_data.polls.parser").setLevel(logging.DEBUG)

sys.path.insert(0, "src")
from lawdigest_data.polls.parser import PollResultParser

pp = PollResultParser(registry_path=Path("config/parser_registry.json"))
results = pp.parse_pdf(Path("파일명.pdf"), pollster_hint="기관명")

print(f"{len(results)}건")
for r in results:
    pcts = " / ".join(f"{p:.1f}" for p in r.overall_percentages)
    print(f"  Q{r.question_number}: {r.question_title} | n={r.overall_n_completed} | {pcts}")
```

### 4.5단계: 파싱 실패 원인 디버깅

결과가 0건이거나 비율이 비어 있다면 DEBUG 로그를 확인한다.

#### 방법 1: probe_parsers --verbose

```bash
python scripts/polls/probe_parsers.py --target <slug> --verbose
```

각 페이지마다 SKIP 원인이 출력된다:
```
DEBUG [XXX] p1 SKIP: 테이블 수=0 (1개여야 함)
DEBUG [XXX] p2 SKIP: 메타 페이지
DEBUG [XXX] p5 OK: q='정당지지도' n=500 opts=8 pcts=[47.0, 40.0, 1.0]
```

#### 파서 내 DEBUG 로그 작성 규칙

새 파서 클래스에는 반드시 단계별 SKIP 원인을 `_logger.debug()`로 기록한다.

```python
_logger.debug("[XXX] p%d SKIP: 사유 (%r)", pg, 추가_컨텍스트)
_logger.debug("[XXX] p%d OK: q='%s' n=%s opts=%d pcts=%s", pg, q_title, n, len(opts), pcts[:3])
```

**SKIP 체크리스트** — 이 순서로 조건을 확인하고 각각 debug 로그를 남긴다:

| 순서 | 조건 | 로그 키워드 |
|------|------|------------|
| 1 | 메타 페이지 (조사개요 등) | `SKIP: 메타 페이지` |
| 2 | 테이블 수 불일치 | `SKIP: 테이블 수=N` |
| 3 | 테이블 행 부족 | `SKIP: 테이블 행 부족` |
| 4 | 질문 제목 미발견 | `SKIP: 질문 제목 미발견` |
| 5 | 선택지 없음 | `SKIP: 선택지 없음 (header=...)` |
| 6 | 전체 행 미발견 | `SKIP: 전체 행 미발견` |
| 7 | n_completed 추출 실패 | `SKIP: n_completed 추출 실패` |
| 8 | 비율 추출 실패 | `SKIP: 비율 추출 실패 (cells=...)` |
| 9 | filter 후 길이 0 | `SKIP: filter 후 길이 0` |

### 5단계: 픽스처 검증

```bash
# 픽스처 생성 (스크리닝으로 다운로드된 PDF 기준)
python scripts/dev/generate_parser_fixtures.py --pollster "기관명 키워드" --force

# 테스트 실행
python -m pytest tests/polls/ -x -q
```

**픽스처 파일:** `tests/polls/fixtures/{pdf_stem}.json`

**검증 항목:**
- `question_count > 0`
- 각 질문의 `overall_percentages` 합계가 75~115% 범위
- `response_options` 개수 = `overall_percentages` 개수

### 6단계: 커밋 & PR

```bash
# 구문 검사
python3 -m py_compile src/lawdigest_data/polls/parser.py && echo OK

# 커밋
git add src/lawdigest_data/polls/parser.py config/parser_registry.json tests/polls/fixtures/
git commit -m "feat: {기관명} 파서 추가"

# PR 본문은 반드시 파일로 작성
gh pr create --title "{기관명} 파서 개발" --body-file /tmp/pr_body.md
```

---

## 파서 선택 로직

`PollResultParser.parse_pdf(pdf_path, pollster_hint)` 호출 시:

1. `pollster_hint`에서 `parser_registry.json`의 `pollster_names` 키워드 매칭
2. 매칭되면 해당 파서 클래스 사용
3. 미매칭 시 `UnknownPollsterError` 발생

```python
from pathlib import Path
from lawdigest_data.polls.parser import PollResultParser

pp = PollResultParser(registry_path=Path("config/parser_registry.json"))
results = pp.parse_pdf(Path("파일명.pdf"), pollster_hint="(주)한길리서치")
```

---

## 기존 파서 포맷 레퍼런스

새 파서 작성 시 유사한 포맷의 기존 파서 코드를 구조 참고용으로 활용한다.

| 파서 클래스 | 질문 마커 | 전체 행 마커 | 비율 위치 | 특이사항 |
|-------------|-----------|--------------|-----------|----------|
| `_TableFormatParser` | `문N)`, `N번)` | `▣ 전체 ▣` | table_cell | 기본 크로스탭 구조 |
| `_RealMeterParser` | `N.` | `전체` | mixed | 헤더 선택지 + 텍스트 비율 |
| `_EmbrainPublicParser` | `[표N]` | `■ 전체 ■` | table_cell | col4+ 선택지 |
| `_KoreanResearchParser` | `[표N]`, `[문N]` | `▣ 전체 ▣` | table_cell | 페이지 분할 merge |
| `_SignalPulseParser` | `[표N]`, `[QN]` | `▣ 전체 ▣` | table_cell | 두 버전 분기 |
| `_FlowerResearchParser` | (cid 인코딩) | `전체` | table_cell | GID→Unicode 역맵핑 필요 |
| `_KIRParser` | `N. 제목` (outside_text) | `합계`/`전체` | table_cell (`%` 포함) | 가중값 컬럼 위치 동적 감지 |

---

## 알려진 포맷 패턴 카탈로그

스크리닝 결과 기준 미개발 기관 포맷 요약:

| 기관 | 질문마커 | 전체행 | 비율위치 | 주요 도전 |
|------|---------|--------|----------|-----------|
| 케이스탯리서치 (KBS) | `N)` | `전 체` | text_bundled | 멀티페이지 merge |
| 케이스탯리서치 (12.31) | 탐지 안 됨 | `계` | text_bundled | 질문 마커 수동 확인 |
| 윈지코리아컨설팅 (250915) | `QN.` | `전 체` | mixed+뭉침 | 비율 셀 분리 + 멀티페이지 |
| 윈지코리아컨설팅 (260305) | `QN.` | `전체` | mixed+뭉침 | 비율 셀 분리 |
| 넥스트리서치 | `N.` | `계` | mixed+뭉침 | 비율 셀 분리 |
| 에스티아이 | `QN.` | `계` | mixed+뭉침 | 비율 셀 분리 + 멀티페이지 |
| 입소스 | `문N.` | `전 체` | text_bundled | 멀티페이지 merge |
| 한길리서치 | `문N)` | `합계` | mixed+뭉침 | 비율 셀 분리 |

> 상세 스크리닝 JSON: `output/polls/screening/{기관명}/`
