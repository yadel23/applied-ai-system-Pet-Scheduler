import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chunk(text="Dogs sleep about 12 hours a day.", source="Dog"):
    return {"text": text, "source": source, "url": "https://en.wikipedia.org/wiki/Dog", "score": 0.8}


def mock_flan(answer_text):
    """Return a (tokenizer, model) mock pair that decodes to answer_text."""
    tokenizer = MagicMock()
    tokenizer.return_value = {}
    tokenizer.decode.return_value = answer_text
    model = MagicMock()
    model.generate.return_value = [MagicMock()]
    return tokenizer, model


# ===========================================================================
# _to_complete_sentences
# ===========================================================================

class TestToCompleteSentences:
    def test_short_text_returned_unchanged(self):
        from chatbot.chat import _to_complete_sentences
        text = "Dogs sleep a lot."
        assert _to_complete_sentences(text, max_chars=400) == text

    def test_trims_at_last_sentence_boundary(self):
        from chatbot.chat import _to_complete_sentences
        text = "Dogs are loyal. They sleep about 12 hours. Extra words that push it over."
        result = _to_complete_sentences(text, max_chars=50)
        assert result.endswith(".")
        assert len(result) <= 50

    def test_falls_back_to_word_boundary_when_no_sentence(self):
        from chatbot.chat import _to_complete_sentences
        text = "Dogs are loyal companions who love to play fetch"
        result = _to_complete_sentences(text, max_chars=20)
        assert result.endswith("...")

    def test_strips_leading_trailing_whitespace(self):
        from chatbot.chat import _to_complete_sentences
        text = "  Dogs sleep a lot.  "
        assert _to_complete_sentences(text, max_chars=400) == "Dogs sleep a lot."

    def test_exact_length_returned_unchanged(self):
        from chatbot.chat import _to_complete_sentences
        text = "Dogs."
        assert _to_complete_sentences(text, max_chars=5) == text


# ===========================================================================
# answer_from_chunks
# ===========================================================================

class TestAnswerFromChunks:
    def test_empty_chunks_returns_fallback_message(self):
        from chatbot.chat import answer_from_chunks
        answer, sources = answer_from_chunks("how long do dogs sleep?", [])
        assert "don't" in answer.lower()
        assert sources == []

    def test_valid_llm_output_is_returned(self):
        from chatbot.chat import answer_from_chunks
        expected = "Dogs typically sleep around 12 hours per day."
        with patch("chatbot.chat.get_flan_model", return_value=mock_flan(expected)):
            answer, _ = answer_from_chunks("how long do dogs sleep?", [make_chunk()])
        assert answer == expected

    def test_sources_extracted_from_chunks(self):
        from chatbot.chat import answer_from_chunks
        with patch("chatbot.chat.get_flan_model", return_value=mock_flan("Dogs sleep 12 hours.")):
            _, sources = answer_from_chunks("how long do dogs sleep?", [make_chunk(source="Dog")])
        assert sources == ["Dog"]

    def test_duplicate_sources_are_deduplicated(self):
        from chatbot.chat import answer_from_chunks
        chunks = [make_chunk(source="Dog"), make_chunk(text="Dogs rest a lot.", source="Dog")]
        with patch("chatbot.chat.get_flan_model", return_value=mock_flan("Dogs sleep 12 hours.")):
            _, sources = answer_from_chunks("how long do dogs sleep?", chunks)
        assert sources.count("Dog") == 1

    def test_multiple_distinct_sources_preserved(self):
        from chatbot.chat import answer_from_chunks
        chunks = [make_chunk(source="Dog"), make_chunk(text="Behavior info.", source="Dog behavior")]
        with patch("chatbot.chat.get_flan_model", return_value=mock_flan("Dogs sleep 12 hours.")):
            _, sources = answer_from_chunks("how long do dogs sleep?", chunks)
        assert set(sources) == {"Dog", "Dog behavior"}

    def test_short_llm_output_triggers_fallback(self):
        from chatbot.chat import answer_from_chunks
        with patch("chatbot.chat.get_flan_model", return_value=mock_flan("12h")):
            answer, _ = answer_from_chunks("how long do dogs sleep?", [make_chunk()])
        assert "don't" in answer.lower()

    def test_malformed_llm_output_triggers_fallback(self):
        from chatbot.chat import answer_from_chunks
        with patch("chatbot.chat.get_flan_model", return_value=mock_flan("1. Dogs sleep and play all day long.")):
            answer, _ = answer_from_chunks("how long do dogs sleep?", [make_chunk()])
        assert "don't" in answer.lower()


# ===========================================================================
# _save_indexed_topics / _load_indexed_topics
# ===========================================================================

class TestIndexedTopics:
    def test_load_returns_empty_list_when_file_missing(self, tmp_path, monkeypatch):
        import chatbot.chat as chat_module
        monkeypatch.setattr(chat_module, "_topics_file", lambda: str(tmp_path / "missing.json"))
        assert chat_module._load_indexed_topics() == []

    def test_save_and_load_round_trip(self, tmp_path, monkeypatch):
        import chatbot.chat as chat_module
        topics_file = str(tmp_path / "indexed_topics.json")
        monkeypatch.setattr(chat_module, "_topics_file", lambda: topics_file)
        monkeypatch.setattr(chat_module, "get_chroma_db_path", lambda: str(tmp_path))
        chat_module._save_indexed_topics(["Dog", "Cat"])
        assert chat_module._load_indexed_topics() == ["Cat", "Dog"]  # sorted on save

    def test_save_sorts_topics(self, tmp_path, monkeypatch):
        import chatbot.chat as chat_module
        topics_file = str(tmp_path / "indexed_topics.json")
        monkeypatch.setattr(chat_module, "_topics_file", lambda: topics_file)
        monkeypatch.setattr(chat_module, "get_chroma_db_path", lambda: str(tmp_path))
        chat_module._save_indexed_topics(["Rabbit", "Dog", "Cat"])
        assert chat_module._load_indexed_topics() == ["Cat", "Dog", "Rabbit"]


# ===========================================================================
# expand_query (retriever)
# ===========================================================================

class TestExpandQuery:
    def test_returns_four_variants(self):
        from pipeline.retriever import expand_query
        assert len(expand_query("how long do dogs sleep?")) == 4

    def test_original_question_is_first(self):
        from pipeline.retriever import expand_query
        q = "how long do dogs sleep?"
        assert expand_query(q)[0] == q

    def test_variants_are_non_empty_strings(self):
        from pipeline.retriever import expand_query
        for variant in expand_query("do dogs need exercise?"):
            assert isinstance(variant, str) and len(variant) > 0
