"""Learn from your edits.

When you fix a transcript by hand, the difference between what Murmur
wrote and what you wanted is exactly a dictionary rule. This module
finds those pairs and teaches the dictionary, so the same mistake is
not made twice.

Conservative on purpose: only short, word-for-word swaps are learned,
and anything the risk checker dislikes is skipped. A full rewrite of a
sentence teaches nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .dictionary import Dictionary, check_risk

MAX_SPAN_WORDS = 4          # longest phrase worth learning, per side
_EDGE_PUNCT = ".,;:!?()[]{}\"'`«»„“”‘’"


@dataclass
class Lesson:
    """What one manual edit taught us."""

    learned: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)


def _clean(words: list[str]) -> str:
    return " ".join(w.strip(_EDGE_PUNCT) for w in words).strip()


def harvest(old: str, new: str) -> Lesson:
    """Word-level diff: every short replaced span is a candidate pair."""
    lesson = Lesson()
    a, b = old.split(), new.split()
    matcher = SequenceMatcher(None, a, b, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "replace":
            continue
        if i2 - i1 > MAX_SPAN_WORDS or j2 - j1 > MAX_SPAN_WORDS:
            continue  # a rewrite, not a correction
        heard = _clean(a[i1:i2])
        written = _clean(b[j1:j2])
        if not heard or not written or heard == written:
            continue
        if check_risk(heard, written) is None:
            lesson.learned.append((heard, written))
        else:
            lesson.skipped.append((heard, written))
    return lesson


def teach(dictionary: Dictionary, old: str, new: str) -> Lesson:
    """Harvest the pairs and write the safe ones into the dictionary."""
    lesson = harvest(old, new)
    for heard, written in lesson.learned:
        dictionary.set_correction(heard, written)
        # A corrected word with its own spelling is also worth biasing
        # the engine toward, so it starts hearing it right.
        if len(written.split()) <= 3 and any(c.isupper() for c in written):
            dictionary.add_term(written)
    return lesson
