"""Provenance: locate the source sentence a summary point came from.

Pure, dependency-free (stdlib only) so it is fully unit-testable without the
LLM. The model emits a ``quote`` alongside each summary point; we re-locate
that quote in the *full* source document by fuzzy-matching it against the
document's sentences, and record the matched sentence's char offsets. A match
below the confidence threshold yields ``None`` — we never fabricate an offset.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

# Minimum similarity (0..1) for a model quote to count as grounded in a source
# sentence. Scoring is by *quote coverage* (how much of the quote is present in
# the sentence), so a short verbatim phrase inside a long sentence still grounds.
DEFAULT_THRESHOLD = 0.6

# Quotes shorter than this (after normalization) are rejected: a 1-2 char quote
# would match almost any sentence and produce meaningless provenance.
_MIN_QUOTE_CHARS = 6

# Split on whitespace that follows sentence-terminal punctuation. Keeps the
# terminator with the sentence it ends. Newlines count as whitespace, so this
# also breaks on line boundaries after a full stop.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

# A period after one of these (or after a single uppercase initial) is an
# abbreviation, not a sentence end — splitting there would fragment a sentence
# and break verbatim-quote grounding.
_ABBREVIATIONS = frozenset(
    {
        "dr",
        "mr",
        "mrs",
        "ms",
        "prof",
        "sr",
        "jr",
        "st",
        "vs",
        "etc",
        "al",
        "fig",
        "no",
        "vol",
        "pp",
        "inc",
        "ltd",
        "co",
        "eg",
        "ie",
        "cf",
        "approx",
        "dept",
        "est",
        "min",
        "max",
    }
)
_TOKEN_BEFORE_DOT = re.compile(r"([A-Za-z]+)\.\Z")


@dataclass(frozen=True)
class SourceSpan:
    """A located source sentence: char offsets into the full document.

    ``start``/``end`` index the full source text such that ``text[start:end]``
    is ``quote``. ``score`` is the quote-coverage confidence (0..1).
    """

    start: int
    end: int
    quote: str
    score: float


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    """Shrink ``[start, end)`` to exclude leading/trailing whitespace."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _is_abbreviation_boundary(text: str, boundary_start: int) -> bool:
    """True if the period just before ``boundary_start`` is an abbreviation dot."""
    if boundary_start == 0 or text[boundary_start - 1] != ".":
        return False
    match = _TOKEN_BEFORE_DOT.search(text[:boundary_start])
    if match is None:
        return False
    token = match.group(1)
    return (len(token) == 1 and token.isupper()) or token.lower() in _ABBREVIATIONS


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Return ``(start, end)`` char-offset spans of the sentences in ``text``.

    Each span covers a sentence's non-whitespace extent, so ``text[start:end]``
    is the verbatim sentence. Abbreviations and initials (``Dr.``, ``U.S.``)
    do not split. Whitespace-only input yields ``[]``.
    """
    spans: list[tuple[int, int]] = []
    pos = 0
    for boundary in _SENTENCE_BOUNDARY.finditer(text):
        if _is_abbreviation_boundary(text, boundary.start()):
            continue
        seg_start, seg_end = _trim(text, pos, boundary.start())
        if seg_end > seg_start:
            spans.append((seg_start, seg_end))
        pos = boundary.end()
    seg_start, seg_end = _trim(text, pos, len(text))
    if seg_end > seg_start:
        spans.append((seg_start, seg_end))
    return spans


def _normalize(s: str) -> str:
    """Lowercase and collapse runs of whitespace, for fuzzy comparison."""
    return " ".join(s.lower().split())


def locate_quote(
    quote: str,
    text: str,
    sentences: list[tuple[int, int]] | None = None,
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> SourceSpan | None:
    """Find the source sentence in ``text`` best matching ``quote``.

    Scored by *quote coverage* — the fraction of the quote present in the
    sentence — so a short verbatim phrase grounds to its (longer) source
    sentence rather than being lost to a length-mismatch penalty. Returns a
    :class:`SourceSpan` (offsets into ``text``) when the best coverage is at
    least ``threshold``, otherwise ``None``. Pass precomputed ``sentences`` to
    avoid re-splitting when locating many quotes against the same source.
    """
    normalized_quote = _normalize(quote)
    if len(normalized_quote) < _MIN_QUOTE_CHARS:
        return None
    if sentences is None:
        sentences = split_sentences(text)

    best: tuple[int, int] | None = None
    best_coverage = 0.0
    best_ratio = 0.0
    matcher = SequenceMatcher(autojunk=False)
    matcher.set_seq1(normalized_quote)
    for start, end in sentences:
        matcher.set_seq2(_normalize(text[start:end]))
        matched = sum(block.size for block in matcher.get_matching_blocks())
        coverage = matched / len(normalized_quote)
        ratio = matcher.ratio()
        # Prefer higher coverage; tie-break toward the tighter-fitting sentence.
        if coverage > best_coverage or (coverage == best_coverage and ratio > best_ratio):
            best, best_coverage, best_ratio = (start, end), coverage, ratio

    if best is None or best_coverage < threshold:
        return None
    start, end = best
    return SourceSpan(start=start, end=end, quote=text[start:end], score=round(best_coverage, 4))
