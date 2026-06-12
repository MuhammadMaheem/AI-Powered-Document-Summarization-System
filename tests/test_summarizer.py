import pytest
from app import create_app
from app.config import TestingConfig


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.test_client() as c:
        yield c


LONG_TEXT = (
    "Artificial intelligence is transforming industries worldwide. "
    "Machine learning enables computers to learn from data without explicit programming. "
    "Deep learning models have achieved remarkable results in image and speech recognition. "
    "Natural language processing allows machines to understand and generate human language. "
    "Organisations are investing heavily in AI research and development. "
    "The healthcare sector uses AI to detect diseases early and improve patient outcomes. "
    "Self-driving vehicles rely on computer vision and reinforcement learning. "
    "AI ethics and governance are increasingly important as these technologies spread. "
    "Data privacy concerns must be addressed carefully in AI systems. "
    "The future workforce will require new skills to work alongside intelligent machines."
)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"


def test_summarize_combined_method(client):
    response = client.post("/api/summarize", json={
        "text": LONG_TEXT,
        "method": "combined",
        "ratio": 0.3,
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["summary"]) > 0
    assert data["original_word_count"] > 0
    assert data["summary_word_count"] < data["original_word_count"]


def test_summarize_frequency_method(client):
    response = client.post("/api/summarize", json={
        "text": LONG_TEXT,
        "method": "frequency",
        "ratio": 0.4,
    })
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_summarize_tfidf_method(client):
    response = client.post("/api/summarize", json={
        "text": LONG_TEXT,
        "method": "tfidf",
        "ratio": 0.3,
    })
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_summarize_returns_analytics(client):
    response = client.post("/api/summarize", json={
        "text": LONG_TEXT,
        "method": "combined",
        "ratio": 0.3,
    })
    data = response.get_json()
    assert "analytics" in data
    assert "top_words" in data["analytics"]
    assert "keywords" in data["analytics"]
    assert "sentence_scores" in data["analytics"]


def test_summarize_text_too_short(client):
    response = client.post("/api/summarize", json={
        "text": "Short text.",
        "method": "combined",
        "ratio": 0.3,
    })
    assert response.status_code == 422
    assert response.get_json()["success"] is False


def test_summarize_invalid_method(client):
    response = client.post("/api/summarize", json={
        "text": LONG_TEXT,
        "method": "invalid_method",
        "ratio": 0.3,
    })
    assert response.status_code == 422


def test_summarize_no_body(client):
    response = client.post("/api/summarize", content_type="application/json", data="")
    assert response.status_code == 400


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"TEYZIX" in response.data
