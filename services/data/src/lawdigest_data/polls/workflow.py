"""여론조사 파이프라인 워크플로우 매니저 (Airflow step 진입점)."""
from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import asdict
from time import monotonic
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.WorkFlowManager import WorkFlowManager
from .crawler import NesdcCrawler
from .models import ListRecord, PollDetail, PollResultSet
from .targets import PollTarget, load_targets, parse_title_region

logger = logging.getLogger(__name__)

# artifact 저장 디렉터리 (WorkFlowManager와 동일한 위치)
_ARTIFACT_DIR = Path(__file__).resolve().parents[6] / ".airflow_artifacts"

# 파싱 결과 저장 루트 디렉터리
_PARSED_DIR = Path(__file__).resolve().parents[6] / "services" / "data" / "output" / "parsed"

_UNSAFE_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_dirname(name: str) -> str:
    """디렉토리명으로 사용하기 안전한 문자열로 변환한다."""
    name = _UNSAFE_CHARS_RE.sub("_", name)
    name = name.strip(". ")
    return name or "_"


def _save_parsed_result(result_set_dict: Dict[str, Any], detail: PollDetail) -> Path:
    """파싱 결과를 output/parsed/{선거명}/{지역명}/{기관명}/{보고서명}.json 에 저장한다."""
    election_name = _safe_dirname(detail.election_name or "미분류")
    region = _safe_dirname(detail.region or "미분류")
    pollster = _safe_dirname(detail.pollster or detail.list_pollster or "미분류")
    report_stem = _safe_dirname(Path(detail.analysis_filename or detail.registration_number).stem)

    out_dir = _PARSED_DIR / election_name / region / pollster
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report_stem}.json"
    out_path.write_text(
        json.dumps(result_set_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


def _write_artifact(prefix: str, payload: Any) -> str:
    _ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = _ARTIFACT_DIR / f"{prefix}_{uuid.uuid4().hex}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    return str(path)


def _read_artifact(artifact_path: str) -> Any:
    return json.loads(Path(artifact_path).read_text(encoding="utf-8"))


def _elapsed_seconds(started_at: float) -> float:
    return round(monotonic() - started_at, 3)


class PollsWorkflowManager:
    """NESDC 여론조사 데이터 파이프라인 오케스트레이터.

    Airflow DAG의 각 Task에서 step 메서드를 호출한다.
    execution_mode는 WorkFlowManager와 동일한 규칙을 따른다:
      dry_run  : DB 미반영
      test_db  : 테스트 DB
      prod     : 운영 DB
    """

    def __init__(self, execution_mode: str = "dry_run") -> None:
        self.mode = WorkFlowManager.normalize_execution_mode(execution_mode)

    def _build_db_manager(self):
        from ..connectors.PollsDatabaseManager import PollsDatabaseManager
        # WorkFlowManager._build_db_manager 패턴을 그대로 따름
        wfm = WorkFlowManager(self.mode)
        base_db = wfm._build_db_manager(self.mode)
        return PollsDatabaseManager(
            host=base_db.host,
            port=base_db.port,
            username=base_db.username,
            password=base_db.password,
            database=base_db.database,
        )

    # ── 카탈로그 스캔 파이프라인 ───────────────────────────────────────────────

    def catalog_scan_step(
        self,
        max_pages: int = 500,
        skip_errors: bool = True,
    ) -> Dict[str, Any]:
        """전체 NESDC 페이지를 스캔하여 모든 여론조사 레코드를 수집한다.

        Returns:
            {mode, total, artifact_path}
        """
        logger.info("[polls_catalog.scan] mode=%s max_pages=%d", self.mode, max_pages)
        crawler = NesdcCrawler(verify_connectivity=True)
        records = crawler.crawl_all_pages(max_pages=max_pages, skip_errors=skip_errors)

        if not records:
            logger.info("[polls_catalog.scan] 수집된 레코드 없음")
            return {"mode": self.mode, "total": 0, "artifact_path": None}

        payload = [asdict(r) for r in records]
        artifact_path = _write_artifact("polls_catalog_scan", payload)
        logger.info("[polls_catalog.scan] 수집 완료: %d건", len(records))
        return {"mode": self.mode, "total": len(records), "artifact_path": artifact_path}

    def save_catalog_step(self, artifact_path: Optional[str]) -> Dict[str, Any]:
        """카탈로그 스캔 결과를 분석하고 DB에 저장한다.

        고유한 (election_type, region, election_name, pollster) 조합을 추출해
        PollCatalog 테이블에 upsert한다.

        Returns:
            {mode, unique_election_types, unique_regions, unique_election_names,
             unique_pollsters, catalog_path}
        """
        logger.info("[polls_catalog.save] mode=%s artifact=%s", self.mode, artifact_path)
        if not artifact_path:
            return {
                "mode": self.mode,
                "unique_election_types": 0,
                "unique_regions": 0,
                "unique_election_names": 0,
                "unique_pollsters": 0,
                "catalog_path": None,
            }

        raw_records = _read_artifact(artifact_path)
        records = [ListRecord(**r) for r in raw_records]

        # 고유 조합 추출
        election_types: set = set()
        regions: set = set()
        election_names_set: set = set()
        pollsters: set = set()
        catalog_rows: List[Dict[str, Any]] = []

        for r in records:
            parsed_region, parsed_election_name = parse_title_region(r.title_region)
            election_types.add(r.province)  # province가 선거구분에 해당
            regions.add(parsed_region)
            election_names_set.add(parsed_election_name)
            pollsters.add(r.pollster)
            catalog_rows.append({
                "election_type": r.province,
                "region": parsed_region,
                "election_name": parsed_election_name,
                "pollster": r.pollster,
                "last_seen_date": r.registered_date,
            })

        # catalog JSON 저장
        catalog_path = _write_artifact("polls_catalog_result", {
            "election_types": sorted(election_types),
            "regions": sorted(regions),
            "election_names": sorted(election_names_set),
            "pollsters": sorted(pollsters),
            "rows": catalog_rows,
        })

        # DB upsert (prod/test_db 모드에서만)
        if self.mode != "dry_run" and catalog_rows:
            db = self._build_db_manager()
            db.ensure_tables()
            upserted = db.upsert_catalog(catalog_rows)
            logger.info("[polls_catalog.save] [%s] catalog upserted=%d", self.mode, upserted)
        else:
            logger.info(
                "[polls_catalog.save] [DRY_RUN] %d건 카탈로그 (DB 미반영)", len(catalog_rows)
            )

        return {
            "mode": self.mode,
            "unique_election_types": len(election_types),
            "unique_regions": len(regions),
            "unique_election_names": len(election_names_set),
            "unique_pollsters": len(pollsters),
            "catalog_path": catalog_path,
        }

    # ── 타겟 기반 수집 파이프라인 ─────────────────────────────────────────────

    def fetch_polls_step(
        self,
        targets_path: Optional[str] = None,
        max_pages_per_target: int = 50,
        skip_errors: bool = True,
    ) -> Dict[str, Any]:
        """poll_targets.json에서 타겟 목록을 로드하고 NESDC를 검색한다.

        Returns:
            {mode, targets, total, artifact_path}
        """
        started_at = monotonic()
        path = Path(targets_path) if targets_path else None
        targets: List[PollTarget] = load_targets(path)
        logger.info("[polls_ingest.fetch] mode=%s targets=%d", self.mode, len(targets))

        if not targets:
            logger.warning("[polls_ingest.fetch] 수집 대상 타겟이 없습니다. poll_targets.json을 확인하세요.")
            return {
                "mode": self.mode,
                "targets": 0,
                "total": 0,
                "artifact_path": None,
                "target_slugs": [],
                "elapsed_seconds": _elapsed_seconds(started_at),
            }

        crawler = NesdcCrawler(verify_connectivity=True)
        target_records = crawler.crawl_for_targets(
            targets=targets,
            max_pages_per_target=max_pages_per_target,
            skip_errors=skip_errors,
        )

        # {slug: [ListRecord, ...]} → 직렬화
        payload: Dict[str, List[Dict]] = {
            slug: [asdict(r) for r in recs]
            for slug, recs in target_records.items()
        }
        total = sum(len(v) for v in payload.values())
        artifact_path = _write_artifact("polls_ingest_fetch", payload)
        logger.info("[polls_ingest.fetch] 수집 완료: 타겟 %d개, 총 %d건", len(targets), total)
        return {
            "mode": self.mode,
            "targets": len(targets),
            "total": total,
            "artifact_path": artifact_path,
            "target_slugs": [target.slug for target in targets],
            "elapsed_seconds": _elapsed_seconds(started_at),
        }

    def crawl_details_step(
        self,
        artifact_path: Optional[str],
        detail_limit: int = 0,
        skip_errors: bool = True,
    ) -> Dict[str, Any]:
        """목록 레코드에서 상세 페이지를 수집한다.

        Returns:
            {mode, total, artifact_path}
        """
        started_at = monotonic()
        logger.info("[polls_ingest.details] mode=%s artifact=%s", self.mode, artifact_path)
        if not artifact_path:
            return {
                "mode": self.mode,
                "total": 0,
                "artifact_path": None,
                "elapsed_seconds": _elapsed_seconds(started_at),
            }

        raw = _read_artifact(artifact_path)
        # raw: {slug: [{...}, ...]}
        all_records: List[ListRecord] = []
        for recs in raw.values():
            all_records.extend(ListRecord(**r) for r in recs)

        if detail_limit > 0:
            all_records = all_records[:detail_limit]

        crawler = NesdcCrawler(verify_connectivity=True)
        details = crawler.crawl_details(all_records, skip_errors=skip_errors)

        payload = [asdict(d) for d in details]
        artifact_path_out = _write_artifact("polls_ingest_details", payload)
        logger.info("[polls_ingest.details] 상세 수집 완료: %d건", len(details))
        return {
            "mode": self.mode,
            "total": len(details),
            "artifact_path": artifact_path_out,
            "elapsed_seconds": _elapsed_seconds(started_at),
        }

    def parse_results_step(
        self,
        artifact_path: Optional[str],
        registry_path: Optional[str] = None,
        pdf_dir: Optional[str] = None,
        skip_errors: bool = True,
    ) -> Dict[str, Any]:
        """상세 정보에서 결과표 PDF를 다운로드하고 파싱한다.

        Returns:
            {mode, parsed, questions_total, artifact_path}
        """
        started_at = monotonic()
        logger.info("[polls_ingest.parse] mode=%s artifact=%s", self.mode, artifact_path)
        if not artifact_path:
            return {
                "mode": self.mode,
                "parsed": 0,
                "questions_total": 0,
                "artifact_path": None,
                "saved_paths": [],
                "elapsed_seconds": _elapsed_seconds(started_at),
            }

        raw = _read_artifact(artifact_path)
        details = [PollDetail(**d) for d in raw]
        detail_by_reg: Dict[str, PollDetail] = {d.registration_number: d for d in details}

        reg_path = Path(registry_path) if registry_path else None
        _pdf_dir = Path(pdf_dir) if pdf_dir else Path("./pdfs")
        crawler = NesdcCrawler(verify_connectivity=False, registry_path=reg_path)
        result_sets = crawler.crawl_results(
            details=details,
            pdf_dir=_pdf_dir,
            skip_errors=skip_errors,
            registry_path=reg_path,
        )

        questions_total = sum(len(rs.questions) for rs in result_sets)
        payload = []
        saved_paths: List[str] = []
        for rs in result_sets:
            rs_dict = asdict(rs)
            payload.append(rs_dict)
            detail = detail_by_reg.get(rs.registration_number)
            if detail:
                out_path = _save_parsed_result(rs_dict, detail)
                saved_paths.append(str(out_path))
                logger.debug("[polls_ingest.parse] 결과 저장: %s", out_path)

        artifact_path_out = _write_artifact("polls_ingest_results", payload)
        if not result_sets:
            logger.warning(
                "[polls_ingest.parse] 파싱 결과가 0건입니다. "
                "pollster 레지스트리, PDF 포맷, 다운로드 상태를 확인하세요."
            )
        logger.info(
            "[polls_ingest.parse] 파싱 완료: %d건, 질문 %d개, 파일 저장 %d건",
            len(result_sets), questions_total, len(saved_paths),
        )
        return {
            "mode": self.mode,
            "parsed": len(result_sets),
            "questions_total": questions_total,
            "artifact_path": artifact_path_out,
            "saved_paths": saved_paths,
            "elapsed_seconds": _elapsed_seconds(started_at),
        }

    def upsert_polls_step(self, artifact_path: Optional[str]) -> Dict[str, Any]:
        """파싱된 여론조사 결과를 DB에 저장한다.

        Returns:
            {mode, upserted_surveys, upserted_questions}
        """
        started_at = monotonic()
        logger.info("[polls_ingest.upsert] mode=%s artifact=%s", self.mode, artifact_path)
        if not artifact_path:
            return {
                "mode": self.mode,
                "upserted_surveys": 0,
                "upserted_questions": 0,
                "elapsed_seconds": _elapsed_seconds(started_at),
            }

        raw = _read_artifact(artifact_path)
        result_sets = [PollResultSet(**rs) for rs in raw]

        if self.mode == "dry_run":
            questions_total = sum(len(rs.questions) for rs in result_sets)
            logger.info(
                "[polls_ingest.upsert] [DRY_RUN] %d건 여론조사, 질문 %d개 (DB 미반영)",
                len(result_sets), questions_total,
            )
            return {
                "mode": self.mode,
                "upserted_surveys": 0,
                "upserted_questions": 0,
                "elapsed_seconds": _elapsed_seconds(started_at),
            }

        db = self._build_db_manager()
        db.ensure_tables()

        upserted_surveys = 0
        upserted_questions = 0
        for rs in result_sets:
            survey_rows = [{
                "registration_number": rs.registration_number,
                "source_url": rs.source_url,
                "pdf_path": rs.pdf_path,
            }]
            upserted_surveys += db.upsert_surveys(survey_rows)

            for q in rs.questions:
                q_rows = [{
                    "registration_number": rs.registration_number,
                    "question_number": q.question_number,
                    "question_title": q.question_title,
                    "n_completed": q.overall_n_completed,
                    "n_weighted": q.overall_n_weighted,
                }]
                q_id = db.upsert_questions(q_rows)
                if q_id:
                    options = [
                        {"option_name": opt, "percentage": pct}
                        for opt, pct in zip(q.response_options, q.overall_percentages)
                    ]
                    upserted_questions += db.replace_options(q_id, options)

        logger.info(
            "[polls_ingest.upsert] [%s] upserted_surveys=%d, upserted_questions=%d",
            self.mode, upserted_surveys, upserted_questions,
        )
        return {
            "mode": self.mode,
            "upserted_surveys": upserted_surveys,
            "upserted_questions": upserted_questions,
            "elapsed_seconds": _elapsed_seconds(started_at),
        }
