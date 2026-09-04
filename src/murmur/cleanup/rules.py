"""Free tidy up. No internet, no key, takes under a millisecond.

It only makes changes that are safe. It never guesses at your meaning.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

# Filler words, only when they stand alone as a whole word.
# "like" and "so" are left out on purpose. They are often real words.
FILLERS = [
    "um", "umm", "uh", "uhh", "er", "erm", "ah", "hmm", "mmm",
]

_FILLER_RE = re.compile(
    r"(?<![\w'])(?:" + "|".join(FILLERS) + r")(?![\w'])[,]?\s*",
    flags=re.IGNORECASE,
)

# "you know" / "I mean" only when fenced by commas, so real uses survive.
_PHRASE_RE = re.compile(
    r",\s*(?:you know|i mean|sort of|kind of)\s*,",
    flags=re.IGNORECASE,
)

# A word said twice in a row: "the the cat" -> "the cat"
_STUTTER_RE = re.compile(r"\b(\w+)(\s+\1\b)+", flags=re.IGNORECASE)

# A short phrase said twice: "can you can you send" -> "can you send"
_PHRASE_STUTTER_RE = re.compile(
    r"\b((?:\w+\s+){1,3}?)\1", flags=re.IGNORECASE
)

# Spoken layout commands.
# Spaces either side are swallowed, so no gap is left before the break.
_SPOKEN = [
    (re.compile(r"[ \t]*\bnew paragraph\b[.,]?[ \t]*", re.IGNORECASE), "\n\n"),
    (re.compile(r"[ \t]*\bnew line\b[.,]?[ \t]*", re.IGNORECASE), "\n"),
]

_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.!?;:])")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_SENTENCE_START = re.compile(r"(^|[.!?]\s+|\n\s*)([a-z])")


class RulesCleaner:
    name = "rules"

    def clean(self, text: str, terms: Sequence[str] = ()) -> str:
        del terms  # the rules cleaner does not need your word list
        if not text:
            return text
        original = text

        text = _PHRASE_RE.sub(", ", text)
        text = _FILLER_RE.sub("", text)
        text = _STUTTER_RE.sub(r"\1", text)
        text = _PHRASE_STUTTER_RE.sub(r"\1", text)

        for pattern, replacement in _SPOKEN:
            text = pattern.sub(replacement, text)

        text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
        text = _MULTI_SPACE.sub(" ", text)
        text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
        text = text.strip()

        # Capital letter at the start of each sentence.
        text = _SENTENCE_START.sub(lambda m: m.group(1) + m.group(2).upper(), text)

        # Full stop at the end, if it ends on a word.
        if text and text[-1].isalnum():
            text += "."

        # Safety net: if the rules ate the whole thing, keep the original.
        return text if text.strip() else original.strip()
