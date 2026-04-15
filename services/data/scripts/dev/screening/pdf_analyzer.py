"""PDF 기본 구조 분석기."""
from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Tuple

from .models import BasicInfo, PageInfo


class AnalyzedPdf:
    """PDF 분석 결과 (불변 데이터 컨테이너).

    pattern_detector와 parser_tester가 공유하여 중복 PDF 열기를 방지한다.
    """

    def __init__(
        self,
        basic_info: BasicInfo,
        pages: List[PageInfo],
        pages_data: List[Tuple[str, List[List[List[Any]]], str]],
        full_text: str,
        per_page_texts: List[str],
        error: Optional[str] = None,
    ) -> None:
        self.basic_info = basic_info
        self.pages = pages
        # parser_tester용: (outside_text, tables, full_text) per page
        self.pages_data = pages_data
        # pattern_detector용
        self.full_text = full_text
        self.per_page_texts = per_page_texts
        self.error = error


class PdfAnalyzer:
    """PyMuPDF(fitz) 기반 PDF 구조 분석기."""

    def analyze(self, pdf_path: Path, sample_pages: int = 5) -> AnalyzedPdf:
        """PDF를 분석하여 AnalyzedPdf를 반환한다.

        Args:
            pdf_path: 분석할 PDF 경로
            sample_pages: 상세 분석할 페이지 수 (기본 5). 전체 텍스트는 항상 추출.
        """
        try:
            import fitz
        except ImportError:
            return AnalyzedPdf(
                BasicInfo(), [], [], "", [],
                error="pymupdf 미설치 (pip install pymupdf)",
            )

        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            return AnalyzedPdf(BasicInfo(), [], [], "", [], error=str(e))

        basic_info = BasicInfo(
            page_count=len(doc),
            file_size_bytes=pdf_path.stat().st_size if pdf_path.exists() else 0,
        )

        pages: List[PageInfo] = []
        pages_data: List[Tuple[str, List, str]] = []
        per_page_texts: List[str] = []
        cid_total = 0

        try:
            for page_num, page in enumerate(doc):
                finder = page.find_tables()
                full_text = page.get_text()
                outside_text = self._extract_outside_text(page, finder)
                tables = [t.extract() for t in finder.tables]

                per_page_texts.append(full_text)
                pages_data.append((outside_text, tables, full_text))

                cid_count = full_text.count("(cid:")
                cid_total += cid_count

                if page_num < sample_pages:
                    page_info = PageInfo(
                        page_num=page_num + 1,
                        table_count=len(tables),
                        text_length=len(full_text),
                        outside_text_length=len(outside_text),
                        cid_count=cid_count,
                    )
                    for tbl in tables:
                        if tbl:
                            rows = len(tbl)
                            cols = max(len(r) for r in tbl) if tbl else 0
                            page_info.table_shapes.append(f"{rows}행×{cols}열")
                            page_info.table_samples.append(tbl[:5])  # 첫 5행

                    page_info.outside_text_sample = outside_text[:800]
                    pages.append(page_info)

            doc.close()

        except Exception as e:
            doc.close()
            return AnalyzedPdf(basic_info, pages, pages_data, "", per_page_texts, error=str(e))

        full_text_all = "\n".join(per_page_texts)

        # cid 인코딩 판정 (전체 페이지 기준, 10개 이상이면 인코딩 문제로 판단)
        basic_info.cid_encoded = cid_total > 10
        basic_info.needs_gid_decode = basic_info.cid_encoded
        basic_info.text_extractable = bool(full_text_all.strip()) and not basic_info.cid_encoded

        return AnalyzedPdf(
            basic_info=basic_info,
            pages=pages,
            pages_data=pages_data,
            full_text=full_text_all,
            per_page_texts=per_page_texts,
        )

    @staticmethod
    def _extract_outside_text(page: Any, finder: Any) -> str:
        """테이블 외부 텍스트만 추출한다."""
        table_bboxes = [t.bbox for t in finder.tables]

        def _in_table(wx0: float, wy0: float, wx1: float, wy1: float) -> bool:
            return any(
                wx0 >= tx0 - 3 and wy0 >= ty0 - 3 and wx1 <= tx1 + 3 and wy1 <= ty1 + 3
                for tx0, ty0, tx1, ty1 in table_bboxes
            )

        words = [w for w in page.get_text("words") if not _in_table(w[0], w[1], w[2], w[3])]
        words.sort(key=lambda w: (round(w[1]), w[0]))

        lines: List[str] = []
        current_y: Optional[float] = None
        line_words: List[str] = []
        for w in words:
            y = round(w[1])
            if current_y is None or abs(y - current_y) > 3:
                if line_words:
                    lines.append(" ".join(line_words))
                current_y, line_words = y, [w[4]]
            else:
                line_words.append(w[4])
        if line_words:
            lines.append(" ".join(line_words))
        return "\n".join(lines)
