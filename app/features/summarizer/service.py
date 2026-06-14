"""
Summarisation service.

Orchestrates:
  1. Preprocessing pipeline
  2. Chosen scoring algorithm(s)
  3. Sentence ranking and selection
  4. Analytics computation
  5. Response assembly

Keeping this logic in a service layer means the Flask route stays a
thin HTTP adapter (parse → call → respond).
"""

from app.features.preprocessor import pipeline as preprocessor
from app.core.algorithms import frequency_scorer, tfidf_scorer, sentence_ranker
from app.core.algorithms.abstractive_summarizer import (
    summarize_abstractive,
    AbstractiveNotAvailable,
)
from app.features.analytics import frequency, keywords, scoring
from app.features.summarizer.schemas import SummarizeRequest, SummarizeResponse
from app.features.summarizer.exceptions import SummarizationError


def summarize(req: SummarizeRequest) -> SummarizeResponse:
    result = preprocessor.run(req.text)

    if len(result.raw_sentences) < 2:
        raise SummarizationError("Text is too short to summarize (fewer than 2 sentences detected).")

    # Analytics always run on the preprocessed tokens regardless of method
    top_words = frequency.top_word_frequencies(result.flat_tokens, top_n=15)
    extracted_keywords = keywords.extract_keywords(result.raw_sentences, result.token_lists, top_n=10)

    if req.method == "abstractive":
        try:
            summary = summarize_abstractive(req.text, ratio=req.ratio)
        except AbstractiveNotAvailable as exc:
            raise SummarizationError(str(exc))

        # Sentence scores still computed extractively for the analytics panel
        freq_scores  = frequency_scorer.score_sentences(result.raw_sentences, result.token_lists)
        tfidf_scores = tfidf_scorer.score_sentences(result.raw_sentences, result.token_lists)
        _, combined_scores = sentence_ranker.rank_and_select(
            result.raw_sentences, freq_scores, tfidf_scores, ratio=req.ratio
        )
        sentence_score_data = scoring.build_sentence_scores(result.raw_sentences, combined_scores)

        orig_words = len(req.text.split())
        summ_words = len(summary.split())
        saved = max(0, 100 - round((summ_words / orig_words) * 100)) if orig_words else 0

        return SummarizeResponse(
            summary=summary,
            original_word_count=orig_words,
            summary_word_count=summ_words,
            compression_ratio=f"{saved}%",
            top_words=top_words,
            keywords=extracted_keywords,
            sentence_scores=sentence_score_data,
            detected_language=result.language,
            detected_language_name=result.language_name,
            summary_type="abstractive",
        )

    # Extractive path (frequency / tfidf / combined)
    freq_scores  = frequency_scorer.score_sentences(result.raw_sentences, result.token_lists)
    tfidf_scores = tfidf_scorer.score_sentences(result.raw_sentences, result.token_lists)

    if req.method == "frequency":
        final_freq   = freq_scores
        final_tfidf  = [0.0] * len(result.raw_sentences)
    elif req.method == "tfidf":
        final_freq   = [0.0] * len(result.raw_sentences)
        final_tfidf  = tfidf_scores
    else:
        final_freq   = freq_scores
        final_tfidf  = tfidf_scores

    summary_sentences, combined_scores = sentence_ranker.rank_and_select(
        result.raw_sentences, final_freq, final_tfidf, ratio=req.ratio
    )

    summary = " ".join(summary_sentences)
    sentence_score_data = scoring.build_sentence_scores(result.raw_sentences, combined_scores)

    orig_words = len(req.text.split())
    summ_words = len(summary.split())
    saved = max(0, 100 - round((summ_words / orig_words) * 100)) if orig_words else 0

    return SummarizeResponse(
        summary=summary,
        original_word_count=orig_words,
        summary_word_count=summ_words,
        compression_ratio=f"{saved}%",
        top_words=top_words,
        keywords=extracted_keywords,
        sentence_scores=sentence_score_data,
        detected_language=result.language,
        detected_language_name=result.language_name,
        summary_type="extractive",
    )
