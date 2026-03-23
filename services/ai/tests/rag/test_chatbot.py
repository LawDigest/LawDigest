import pytest
from unittest.mock import MagicMock, patch


def test_chatbot_answer_returns_string(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.chatbot import LawdigestionChatbot
    with patch("lawdigest_ai.rag.chatbot.VectorStore") as MockVS, \
         patch("lawdigest_ai.rag.chatbot.EmbeddingGenerator") as MockEG:
        mock_vs = MockVS.return_value
        mock_vs.search.return_value = [
            MagicMock(payload={"bill_id": "B001", "bill_name": "테스트법", "brief_summary": "요약", "gpt_summary": "상세"})
        ]
        mock_eg = MockEG.return_value
        mock_eg.generate.return_value = [0.1] * 1536

        chatbot = LawdigestionChatbot()
        with patch.object(chatbot, "_call_llm", return_value="이것은 답변입니다."):
            result = chatbot.answer("세금 관련 법안이 있나요?")
    assert isinstance(result, str)
