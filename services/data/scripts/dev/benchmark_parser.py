"""pdfplumber vs PyMuPDF 파서 속도 벤치마크."""
from __future__ import annotations

import time
from pathlib import Path

PDF_DIR = Path(__file__).resolve().parents[2] / "output" / "pdfs"


def _progress(current: int, total: int, label: str, elapsed: float) -> None:
    bar_width = 30
    filled = int(bar_width * current / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"\r  [{bar}] {current}/{total}  {elapsed:.1f}s  {label[:40]:<40}", end="", flush=True)


def _bench_pymupdf(pdf_paths: list[Path], run: int, runs: int) -> float:
    import fitz

    print(f"\nPyMuPDF [{run}/{runs}]")
    t0 = time.perf_counter()
    for i, path in enumerate(pdf_paths, 1):
        doc = fitz.open(path)
        try:
            for page in doc:
                page.get_text()
                [t.extract() for t in page.find_tables().tables]
        finally:
            doc.close()
        _progress(i, len(pdf_paths), path.name, time.perf_counter() - t0)
    elapsed = time.perf_counter() - t0
    print(f"\r  완료: {elapsed:.3f}s{' ' * 60}")
    return elapsed


def _bench_pdfplumber(pdf_paths: list[Path], run: int, runs: int) -> float:
    import pdfplumber

    print(f"\npdfplumber [{run}/{runs}]")
    t0 = time.perf_counter()
    for i, path in enumerate(pdf_paths, 1):
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page.extract_text()
                page.extract_tables()
        _progress(i, len(pdf_paths), path.name, time.perf_counter() - t0)
    elapsed = time.perf_counter() - t0
    print(f"\r  완료: {elapsed:.3f}s{' ' * 60}")
    return elapsed


def main() -> None:
    pdf_paths = sorted(PDF_DIR.rglob("*.pdf"))[:5]
    if not pdf_paths:
        print("PDF 파일을 찾을 수 없습니다.")
        return

    print(f"대상 PDF: {len(pdf_paths)}개")
    runs = 1

    print("\n── pdfplumber ─────────────────────────────")
    pdfplumber_times = [_bench_pdfplumber(pdf_paths, i + 1, runs) for i in range(runs)]

    print("\n── PyMuPDF ────────────────────────────────")
    pymupdf_times = [_bench_pymupdf(pdf_paths, i + 1, runs) for i in range(runs)]

    avg_plumber = sum(pdfplumber_times) / runs
    avg_mupdf = sum(pymupdf_times) / runs
    speedup = avg_plumber / avg_mupdf if avg_mupdf > 0 else float("inf")

    print("\n── 결과 ────────────────────────────────────")
    print(f"pdfplumber  평균: {avg_plumber:.3f}s")
    print(f"PyMuPDF     평균: {avg_mupdf:.3f}s")
    print(f"속도 향상:        {speedup:.2f}x")


if __name__ == "__main__":
    main()
