"""Tests for `docsummarizer.provenance` — sentence splitting + quote location.

Pure functions, no model: given a source string and a (model-emitted) quote,
locate the source sentence it came from, by char offsets into the full text.
"""

from __future__ import annotations

from docsummarizer.provenance import SourceSpan, locate_quote, split_sentences


# --------------------------------------------------------------------------- #
# split_sentences — offsets must be exact slices of the source
# --------------------------------------------------------------------------- #
def test_split_sentences_returns_exact_offset_slices() -> None:
    text = "Foo bar. Baz qux! Quux?"
    spans = split_sentences(text)
    assert [text[s:e] for s, e in spans] == ["Foo bar.", "Baz qux!", "Quux?"]


def test_split_sentences_empty_text_is_empty() -> None:
    assert split_sentences("") == []
    assert split_sentences("   \n\n  ") == []


def test_split_sentences_no_terminal_punctuation_is_one_span() -> None:
    text = "a heading with no full stop"
    spans = split_sentences(text)
    assert len(spans) == 1
    assert text[spans[0][0] : spans[0][1]] == text


def test_split_sentences_offsets_are_into_full_text() -> None:
    text = "First sentence here. Second one follows."
    spans = split_sentences(text)
    # The second span must start partway through the document, not at 0.
    assert spans[1][0] > 0
    assert text[spans[1][0] : spans[1][1]] == "Second one follows."


def test_split_sentences_splits_on_newlines_after_punctuation() -> None:
    text = "Line one ends.\nLine two ends."
    spans = split_sentences(text)
    assert [text[s:e] for s, e in spans] == ["Line one ends.", "Line two ends."]


# --------------------------------------------------------------------------- #
# locate_quote — fuzzy-match a quote to the best source sentence
# --------------------------------------------------------------------------- #
_SOURCE = (
    "The Transformer is a model architecture eschewing recurrence. "
    "It relies entirely on an attention mechanism to draw global dependencies. "
    "Experiments show it is superior in quality while being more parallelizable."
)


def test_locate_quote_verbatim_match_returns_that_sentence() -> None:
    quote = "It relies entirely on an attention mechanism to draw global dependencies."
    span = locate_quote(quote, _SOURCE)
    assert span is not None
    assert _SOURCE[span.start : span.end] == quote
    assert span.score >= 0.99


def test_locate_quote_paraphrase_snaps_to_nearest_sentence() -> None:
    # Slightly reworded, but clearly the third sentence.
    quote = "Experiments show the model is superior in quality and more parallelizable."
    span = locate_quote(quote, _SOURCE)
    assert span is not None
    assert "superior in quality" in _SOURCE[span.start : span.end]
    assert 0.6 <= span.score <= 1.0


def test_locate_quote_offsets_map_into_full_source() -> None:
    quote = "The Transformer is a model architecture eschewing recurrence."
    span = locate_quote(quote, _SOURCE)
    assert span is not None
    assert span.start == 0
    assert _SOURCE[span.start : span.end] == quote


def test_locate_quote_unrelated_text_returns_none() -> None:
    assert locate_quote("The mitochondria is the powerhouse of the cell.", _SOURCE) is None


def test_locate_quote_empty_quote_returns_none() -> None:
    assert locate_quote("", _SOURCE) is None
    assert locate_quote("   ", _SOURCE) is None


def test_locate_quote_short_verbatim_fragment_grounds() -> None:
    # A 4-bit model often cites a phrase, not a whole sentence. A verbatim
    # fragment must still ground to its source sentence (coverage, not the
    # symmetric whole-sentence ratio).
    for fragment in ("eschewing recurrence", "attention mechanism", "superior in quality"):
        span = locate_quote(fragment, _SOURCE)
        assert span is not None, fragment
        assert fragment in _SOURCE[span.start : span.end]


def test_locate_quote_threshold_governs_fuzzy_match() -> None:
    # A loose paraphrase (not a verbatim substring) grounds only below a strict
    # threshold — the threshold still governs non-verbatim matches.
    quote = "the model avoids recurrent and convolutional layers"
    assert locate_quote(quote, _SOURCE, threshold=0.99) is None
    assert locate_quote(quote, _SOURCE, threshold=0.1) is not None


def test_locate_quote_rejects_trivially_short_quote() -> None:
    # A 1-2 char "quote" would match almost anything; reject it.
    assert locate_quote("the", _SOURCE) is None


def test_split_sentences_keeps_abbreviations_whole() -> None:
    text = "Dr. Smith left at noon. He went home."
    spans = split_sentences(text)
    assert [text[s:e] for s, e in spans] == ["Dr. Smith left at noon.", "He went home."]


def test_split_sentences_keeps_initials_whole() -> None:
    text = "The U.S. economy grew. Inflation fell."
    spans = split_sentences(text)
    assert [text[s:e] for s, e in spans] == ["The U.S. economy grew.", "Inflation fell."]


def test_locate_quote_grounds_sentence_with_abbreviation() -> None:
    source = "Dr. Smith reported a forty percent gain. The study ended early."
    quote = "Dr. Smith reported a forty percent gain."
    span = locate_quote(quote, source)
    assert span is not None
    assert source[span.start : span.end] == quote


def test_source_span_is_frozen() -> None:
    from dataclasses import FrozenInstanceError

    import pytest

    span = SourceSpan(start=0, end=5, quote="hello", score=1.0)
    with pytest.raises(FrozenInstanceError):
        span.start = 3  # type: ignore[misc]
