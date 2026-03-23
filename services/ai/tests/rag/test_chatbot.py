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


def test_chatbot_call_llm_returns_fallback_on_error(monkeypatch):
    """LLM API 호출 실패 시 _call_llm은 fallback 메시지를 반환해야 한다."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.chatbot import LawdigestionChatbot
    with patch("lawdigest_ai.rag.chatbot.VectorStore"), \
         patch("lawdigest_ai.rag.chatbot.EmbeddingGenerator"), \
         patch("lawdigest_ai.rag.chatbot.OpenAI") as MockOpenAI:
        mock_llm = MockOpenAI.return_value
        mock_llm.chat.completions.create.side_effect = Exception("API error")
        chatbot = LawdigestionChatbot()
        result = chatbot._call_llm("테스트 질문", "테스트 컨텍스트")
    assert "죄송합니다" in result


def test_chatbot_build_context_with_empty_documents(monkeypatch):
    """문서가 없을 때 _build_context는 '관련 법안 정보를 찾을 수 없습니다.' 를 반환해야 한다."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.chatbot import LawdigestionChatbot
    with patch("lawdigest_ai.rag.chatbot.VectorStore"), \
         patch("lawdigest_ai.rag.chatbot.EmbeddingGenerator"), \
         patch("lawdigest_ai.rag.chatbot.OpenAI"):
        chatbot = LawdigestionChatbot()
    context = chatbot._build_context([])
    assert "찾을 수 없습니다" in context


def test_chatbot_retrieve_returns_empty_when_no_vector(monkeypatch):
    """임베딩이 None인 경우 _retrieve는 빈 리스트를 반환해야 한다."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from lawdigest_ai.rag.chatbot import LawdigestionChatbot
    with patch("lawdigest_ai.rag.chatbot.VectorStore"), \
         patch("lawdigest_ai.rag.chatbot.EmbeddingGenerator"), \
         patch("lawdigest_ai.rag.chatbot.OpenAI"):
        chatbot = LawdigestionChatbot()
        chatbot.embedder = MagicMock()
        chatbot.embedder.generate.return_value = None
        results = chatbot._retrieve("테스트 쿼리")
    assert results == []
