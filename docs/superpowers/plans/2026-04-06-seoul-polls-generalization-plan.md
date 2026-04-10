# 서울시 여론조사 확장 및 광역시·도 일반화 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 서울특별시장 여론조사 수집/파싱을 추가하면서, 경기도 전용에 가까운 현재 타겟 구조를 광역시·도 공통 구조로 일반화한다.

**Architecture:** `services/data/config/poll_targets.json`를 지역/선거/타겟 3계층 선언 구조로 재편하고, `targets.py`에서 이를 조합한 완성형 타겟 객체를 제공한다. 수집기는 새 타겟 객체가 제공하는 NESDC 검색 파라미터를 그대로 사용하고, 파서 레이어는 서울 PDF를 실제로 적용해 깨지는 조사기관만 최소 수정한다.

**Tech Stack:** Python 3, pytest, PyMuPDF(fitz), BeautifulSoup, requests

---

## 파일 구조 맵

### 핵심 수정 대상

- Modify: `services/data/config/poll_targets.json`
  - 지역/선거/타겟 3계층 설정 구조로 전환
- Modify: `services/data/src/lawdigest_data/polls/targets.py`
  - `RegionSpec`, `ElectionSpec`, 개편된 `PollTarget`, 새 로더/매칭 로직
- Modify: `services/data/src/lawdigest_data/polls/crawler.py`
  - 새 타겟 모델에서 검색 키를 읽도록 조정
- Modify: `services/data/scripts/polls/collect_poll_list.py`
  - 새 타겟 구조 로딩과 로그/usage 정리
- Modify: `services/data/scripts/polls/download_pdfs.py`
- Modify: `services/data/scripts/polls/check_pdfs.py`
- Modify: `services/data/scripts/polls/parse_all.py`
- Modify: `services/data/scripts/polls/probe_parsers.py`
  - slug 기반 실행은 유지하되 새 타겟 구조 사용
- Modify as needed: `services/data/src/lawdigest_data/polls/parser.py`
  - 서울 PDF에서 실제로 필요한 조사기관 파서 보완 또는 신규 추가
- Modify as needed: `services/data/config/parser_registry.json`
  - 신규 조사기관 파서 등록 시 갱신

### 테스트/픽스처

- Create: `services/data/tests/polls/test_targets.py`
  - 새 계층 설정 로딩, 완성형 타겟 조합, 서울/경기 매칭 검증
- Modify: `services/data/tests/polls/test_polls_workflow_metrics.py`
  - 새 설정 구조 반영
- Modify: `services/data/tests/polls/test_targets_ignore.py`
  - ignore 목록이 새 구조에서도 동작하는지 검증
- Modify: `services/data/tests/polls/test_parser_integration.py`
  - 서울 픽스처 포함 상태에서 전체 검증 유지
- Create: `services/data/tests/polls/fixtures/*.json`
  - 서울 PDF 파싱 성공 결과 픽스처

### 문서

- Modify: `services/data/docs/nesdc_search_api.md`
  - 경기 예시 중심 설명을 광역시·도 공통 설명으로 정리
- Modify: `services/data/docs/parser_development_status.md`
  - 서울 추가 진행 현황 반영

## Task 1: 타겟 설정 구조 개편

**Files:**
- Modify: `services/data/config/poll_targets.json`
- Create: `services/data/tests/polls/test_targets.py`

- [ ] **Step 1: 새 설정 구조를 검증하는 실패 테스트 작성**

```python
def test_load_targets_builds_region_and_election_backed_targets(tmp_path):
    config = {
        "regions": {
            "gyeonggi": {"search_cnd": "4", "search_wrd": "경기도", "region": "경기도 전체"},
            "seoul": {"search_cnd": "4", "search_wrd": "서울특별시", "region": "서울특별시 전체"},
        },
        "elections": {
            "local_9th_governor": {
                "poll_gubuncd": "VT026",
                "election_type": "제9회 전국동시지방선거",
                "election_names": ["광역단체장선거"],
            }
        },
        "targets": [
            {"slug": "gyeonggi_governor_9th", "region_key": "gyeonggi", "election_key": "local_9th_governor"},
            {"slug": "seoul_mayor_9th", "region_key": "seoul", "election_key": "local_9th_governor"},
        ],
    }
```

- [ ] **Step 2: 실패를 확인**

Run: `cd services/data && pytest tests/polls/test_targets.py -v`
Expected: FAIL because loader/model does not understand `regions` / `elections` / `region_key`

- [ ] **Step 3: 최소 구현으로 새 구조 로더 추가**

```python
@dataclass(frozen=True)
class RegionSpec: ...

@dataclass(frozen=True)
class ElectionSpec: ...

@dataclass(frozen=True)
class PollTarget:
    slug: str
    region_key: str
    election_key: str
    ...
```

- [ ] **Step 4: 기본 설정 파일을 새 구조로 치환**

`services/data/config/poll_targets.json`에 최소한 아래 타겟이 존재하도록 변경한다.

- `gyeonggi_governor_9th`
- `seoul_mayor_9th`

- [ ] **Step 5: 테스트 재실행**

Run: `cd services/data && pytest tests/polls/test_targets.py -v`
Expected: PASS

- [ ] **Step 6: 커밋**

```bash
git add services/data/config/poll_targets.json services/data/src/lawdigest_data/polls/targets.py services/data/tests/polls/test_targets.py
git commit -m "refactor: 여론조사 타겟 구조를 지역·선거 계층으로 개편"
```

## Task 2: 타겟 매칭과 워크플로우 테스트 전환

**Files:**
- Modify: `services/data/src/lawdigest_data/polls/targets.py`
- Modify: `services/data/tests/polls/test_targets_ignore.py`
- Modify: `services/data/tests/polls/test_polls_workflow_metrics.py`

- [ ] **Step 1: 서울/경기 매칭 케이스 실패 테스트 추가**

```python
def test_matches_target_distinguishes_seoul_from_gyeonggi():
    record = ListRecord(title_region="서울특별시 전체 광역단체장선거", ...)
    assert matches_target(record, seoul_target) is True
    assert matches_target(record, gyeonggi_target) is False
```

- [ ] **Step 2: 실패 확인**

Run: `cd services/data && pytest tests/polls/test_targets.py tests/polls/test_targets_ignore.py tests/polls/test_polls_workflow_metrics.py -v`
Expected: FAIL with old fixture/config assumptions

- [ ] **Step 3: `matches_target()`와 ignore 관련 테스트 갱신**

```python
region, election_name = parse_title_region(record.title_region)
if target.region is not None and region != target.region:
    return False
```

- [ ] **Step 4: 워크플로우 테스트의 인라인 설정 JSON을 새 구조로 교체**

`test_polls_workflow_metrics.py`의 `targets_path.write_text(...)` 블록을 `regions/elections/targets` 구조로 갱신한다.

- [ ] **Step 5: 테스트 재실행**

Run: `cd services/data && pytest tests/polls/test_targets.py tests/polls/test_targets_ignore.py tests/polls/test_polls_workflow_metrics.py -v`
Expected: PASS

- [ ] **Step 6: 커밋**

```bash
git add services/data/src/lawdigest_data/polls/targets.py services/data/tests/polls/test_targets_ignore.py services/data/tests/polls/test_polls_workflow_metrics.py services/data/tests/polls/test_targets.py
git commit -m "test: 서울·경기 타겟 매칭과 워크플로우 테스트 갱신"
```

## Task 3: 수집 스크립트와 크롤러를 새 타겟 구조로 전환

**Files:**
- Modify: `services/data/src/lawdigest_data/polls/crawler.py`
- Modify: `services/data/scripts/polls/collect_poll_list.py`
- Modify: `services/data/scripts/polls/download_pdfs.py`
- Modify: `services/data/scripts/polls/check_pdfs.py`
- Modify: `services/data/scripts/polls/parse_all.py`
- Modify: `services/data/scripts/polls/probe_parsers.py`

- [ ] **Step 1: 서울 slug 선택 동작을 검증하는 실패 테스트 또는 스모크 케이스 정의**

우선 테스트가 없으면 `test_targets.py` 또는 `test_polls_workflow_metrics.py`에 아래 수준의 회귀 케이스를 추가한다.

```python
assert [t.slug for t in load_targets(path)] == ["gyeonggi_governor_9th", "seoul_mayor_9th"]
```

- [ ] **Step 2: 실패 확인**

Run: `cd services/data && pytest tests/polls/test_targets.py tests/polls/test_polls_workflow_metrics.py -v`
Expected: FAIL if any script/crawler path still depends on old fields

- [ ] **Step 3: 크롤러와 스크립트에서 새 타겟 필드 사용**

구현 포인트:

- `crawl_for_targets()`는 계속 `(poll_gubuncd, search_cnd, search_wrd)` 조합을 사용
- 각 스크립트의 usage/help/examples에서 경기 전용 표현 제거
- 기본 타겟 선택은 유지하되, `--target seoul_mayor_9th`가 동작하도록 보장

- [ ] **Step 4: 스모크 테스트**

Run: `cd services/data && pytest tests/polls/test_targets.py tests/polls/test_polls_workflow_metrics.py -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add services/data/src/lawdigest_data/polls/crawler.py services/data/scripts/polls/collect_poll_list.py services/data/scripts/polls/download_pdfs.py services/data/scripts/polls/check_pdfs.py services/data/scripts/polls/parse_all.py services/data/scripts/polls/probe_parsers.py services/data/tests/polls/test_targets.py services/data/tests/polls/test_polls_workflow_metrics.py
git commit -m "refactor: 여론조사 수집 스크립트를 광역시도 타겟 구조로 전환"
```

## Task 4: 서울 목록 수집과 조사기관 분포 확인

**Files:**
- Runtime artifacts: `services/data/output/polls/lists/seoul_mayor_9th.json`
- Runtime artifacts: `services/data/output/polls/lists/seoul_mayor_9th.csv`

- [ ] **Step 1: 서울 목록 수집 실행**

Run: `cd services/data && python scripts/polls/collect_poll_list.py --target seoul_mayor_9th`
Expected: 서울 타겟 목록 JSON/CSV 생성

- [ ] **Step 2: 수집 결과에서 조사기관 분포 확인**

Run: `cd services/data && python - <<'PY'\nimport json\nfrom collections import Counter\nrows=json.load(open('output/polls/lists/seoul_mayor_9th.json', encoding='utf-8'))\nprint(len(rows))\nprint(Counter(r['pollster'] for r in rows).most_common())\nPY`
Expected: 서울 목록 총건수와 pollster 분포 확인

- [ ] **Step 3: 신규 기관/기존 기관 분류 메모 작성**

`services/data/docs/parser_development_status.md`에 서울 대상 기관 분포와 예상 작업량을 업데이트한다.

- [ ] **Step 4: 커밋**

```bash
git add services/data/docs/parser_development_status.md
git commit -m "docs: 서울 여론조사 기관 분포와 파서 범위를 정리"
```

## Task 5: 서울 PDF 다운로드 및 파서 갭 진단

**Files:**
- Runtime artifacts under: `services/data/output/polls/pdfs/seoul_mayor_9th/`
- Modify as needed: `services/data/src/lawdigest_data/polls/parser.py`
- Modify as needed: `services/data/config/parser_registry.json`

- [ ] **Step 1: 서울 PDF 다운로드**

Run: `cd services/data && python scripts/polls/download_pdfs.py --target seoul_mayor_9th`
Expected: 서울 PDF 파일 저장

- [ ] **Step 2: 기존 파서 재사용 가능성 진단**

Run: `cd services/data && python scripts/polls/probe_parsers.py --target seoul_mayor_9th`
Expected: 기관별 성공/실패 현황 파악

- [ ] **Step 3: 실패 기관용 최소 실패 테스트 추가**

실패 기관이 확인되면 그 기관 PDF를 기준으로 픽스처 또는 진단 기반 테스트를 추가한다.

```python
def test_parser_handles_seoul_pdf_variant(...):
    ...
```

- [ ] **Step 4: 테스트 실패 확인**

Run: `cd services/data && pytest tests/polls/test_parser_integration.py -k seoul -v`
Expected: FAIL for unsupported pollster/format

- [ ] **Step 5: 최소 구현**

- 기존 기관이면 해당 파서 분기 보완
- 신규 기관이면 파서 클래스와 registry 추가

- [ ] **Step 6: 커밋**

```bash
git add services/data/src/lawdigest_data/polls/parser.py services/data/config/parser_registry.json services/data/tests/polls/test_parser_integration.py
git commit -m "feat: 서울 여론조사 PDF 파서 갭을 보완"
```

## Task 6: 서울 픽스처 생성과 통합 테스트 보강

**Files:**
- Create/Modify: `services/data/tests/polls/fixtures/*.json`
- Modify: `services/data/tests/polls/test_parser_integration.py`

- [ ] **Step 1: 서울 파싱 성공 PDF에 대한 픽스처 생성**

Run: `cd services/data && python scripts/dev/generate_parser_fixtures.py --pollster <기관명>`
Expected: 서울 PDF용 fixture JSON 생성

- [ ] **Step 2: 픽스처 로딩 테스트가 서울도 포함하도록 유지**

`test_parser_integration.py`는 fixtures 디렉터리 전체를 자동 로드하므로, 서울 fixture 추가 후 별도 필터 없이 통과해야 한다.

- [ ] **Step 3: 서울/경기 통합 테스트 실행**

Run: `cd services/data && pytest tests/polls/test_parser_integration.py tests/polls/test_parser_validation_unit.py tests/polls/test_table_utils.py -v`
Expected: PASS

- [ ] **Step 4: 커밋**

```bash
git add services/data/tests/polls/fixtures services/data/tests/polls/test_parser_integration.py
git commit -m "test: 서울 여론조사 픽스처와 통합 검증 추가"
```

## Task 7: 문서 정리와 최종 검증

**Files:**
- Modify: `services/data/docs/nesdc_search_api.md`
- Modify: `services/data/docs/parser_development_status.md`
- Modify any touched script docstrings/help text

- [ ] **Step 1: 문서와 usage 문자열을 광역시·도 공통 설명으로 정리**

- [ ] **Step 2: 린트/테스트 최종 실행**

Run: `cd services/data && pytest tests/polls/test_targets.py tests/polls/test_targets_ignore.py tests/polls/test_polls_workflow_metrics.py tests/polls/test_parser_integration.py tests/polls/test_parser_validation_unit.py tests/polls/test_table_utils.py -v`
Expected: PASS

- [ ] **Step 3: 필요 시 추가 정적 검사 실행**

Run: `cd services/data && python -m compileall src`
Expected: PASS without syntax errors

- [ ] **Step 4: 최종 커밋**

```bash
git add services/data/docs/nesdc_search_api.md services/data/docs/parser_development_status.md services/data/src/lawdigest_data/polls services/data/scripts/polls services/data/tests/polls
git commit -m "feat: 서울 여론조사 확장과 광역시도 일반화 완료"
```

## 실행 메모

- 코드 작업 시작 직전에 사용자에게 전용 worktree 생성 여부를 반드시 확인한다.
- 사용자가 worktree를 원하면 `.worktrees/<branch>` 아래에 생성하고 현재 작업 디렉터리에서 직접 수정하지 않는다.
- 코드 구현은 반드시 TDD 순서(실패 테스트 → 실패 확인 → 최소 구현 → 통과 확인)로 진행한다.
