import pytest
from app.features.preprocessor import pipeline
from app.features.preprocessor.text_cleaner import clean_text, remove_stopwords
from app.features.preprocessor.tokenizer import sentence_tokenize, word_tokenize, filter_tokens


TEXT = (
    "Artificial intelligence is transforming modern industries. "
    "Machine learning algorithms can analyse large volumes of data quickly. "
    "Natural language processing enables computers to understand human text. "
    "These technologies are being adopted by organisations worldwide. "
    "The future of AI looks both promising and challenging."
)


def test_clean_text_lowercases():
    result = clean_text("Hello WORLD! Visit https://example.com")
    assert result == result.lower()
    assert "https" not in result


def test_clean_text_removes_urls():
    result = clean_text("See https://example.com for details.")
    assert "example.com" not in result


def test_remove_stopwords_filters_common_words():
    tokens = ["the", "quick", "brown", "fox", "is", "running"]
    result = remove_stopwords(tokens)
    assert "the" not in result
    assert "is" not in result
    assert "quick" in result


def test_sentence_tokenize_splits_correctly():
    sentences = sentence_tokenize(TEXT)
    assert len(sentences) == 5


def test_word_tokenize_produces_list():
    tokens = word_tokenize("Hello world, this is a test.")
    assert isinstance(tokens, list)
    assert len(tokens) > 0


def test_filter_tokens_removes_punctuation():
    tokens = filter_tokens(["hello", "world", "!", ".", "test", "a"])
    assert "!" not in tokens
    assert "." not in tokens
    assert "a" not in tokens  # length filter (<=1)


def test_pipeline_run_returns_correct_structure():
    result = pipeline.run(TEXT)
    assert len(result.raw_sentences) == 5
    assert len(result.token_lists) == 5
    assert len(result.flat_tokens) > 0


def test_pipeline_token_lists_are_cleaned():
    result = pipeline.run(TEXT)
    for token_list in result.token_lists:
        for token in token_list:
            assert token.isalpha()
            assert len(token) > 1
