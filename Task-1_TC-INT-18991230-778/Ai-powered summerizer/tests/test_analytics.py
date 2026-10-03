import pytest
from app.features.analytics.frequency import top_word_frequencies
from app.features.analytics.scoring import build_sentence_scores


TOKENS = ["machine", "learning", "data", "model", "machine", "data", "data", "neural", "network", "machine"]


def test_top_word_frequencies_returns_sorted():
    result = top_word_frequencies(TOKENS, top_n=5)
    assert len(result) <= 5
    # Should be sorted descending by count
    counts = [item["count"] for item in result]
    assert counts == sorted(counts, reverse=True)


def test_top_word_frequencies_correct_top_word():
    result = top_word_frequencies(TOKENS, top_n=3)
    assert result[0]["word"] == "machine"
    assert result[0]["count"] == 3


def test_top_word_frequencies_empty_input():
    result = top_word_frequencies([], top_n=5)
    assert result == []


def test_build_sentence_scores_labels():
    combined = [
        {"sentence": "High importance sentence.", "score": 0.9},
        {"sentence": "Medium importance sentence.", "score": 0.5},
        {"sentence": "Low importance sentence.", "score": 0.2},
    ]
    result = build_sentence_scores(["s1", "s2", "s3"], combined)
    assert result[0]["label"] == "high"
    assert result[1]["label"] == "medium"
    assert result[2]["label"] == "low"


def test_build_sentence_scores_empty():
    result = build_sentence_scores([], [])
    assert result == []
