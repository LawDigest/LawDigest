"""Compatibility wrapper for the AI summarizer.

The implementation now lives in ``services/ai`` so the AI-specific code can be
maintained independently from the data pipeline package.
"""

from lawdigest_ai_summarizer.AISummarizer import AISummarizer, StructuredBillSummary

__all__ = ["AISummarizer", "StructuredBillSummary"]
