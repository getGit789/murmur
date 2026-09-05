"""Free tidy up. No internet, no key, takes under a millisecond.

It only makes changes that are safe. It never guesses at your meaning.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from ..dictionary import WORD_CHAR_RE

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
# OFF unless asked for. Text alone cannot tell a stumble from grammar,
# and these would turn "I had had enough" into "I had enough".
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

    def __init__(self, remove_repeats: bool = False) -> None:
        # `[cleanup] remove_repeats = true` in config.toml switches it on.
        self.remove_repeats = remove_repeats

    def clean(self, text: str, terms: Sequence[str] = ()) -> str:
        """Tidy the text. `terms` are spellings the dictionary already
        put in place; the sentence capital must not overwrite them."""
        if not text:
            return text
        original = text
        keep = _lowercase_starts(terms)

        text = _PHRASE_RE.sub(", ", text)
        text = _FILLER_RE.sub("", text)
        if self.remove_repeats:
            text = _STUTTER_RE.sub(r"\1", text)
            text = _PHRASE_STUTTER_RE.sub(r"\1", text)

        for pattern, replacement in _SPOKEN:
            text = pattern.sub(replacement, text)

        text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
        text = _MULTI_SPACE.sub(" ", text)
        text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
        text = text.strip()

        # Capital letter at the start of each sentence, unless the sentence
        # starts with one of your own spellings, like "iPhone" or "eBay".
        text = _SENTENCE_START.sub(lambda m: _capitalise(m, keep), text)

        # Full stop at the end, if it ends on a word.
        if text and text[-1].isalnum():
            text += "."

        # Safety net: if the rules ate the whole thing, keep the original.
        return text if text.strip() else original.strip()


def _lowercase_starts(terms: Sequence[str]) -> tuple[str, ...]:
    """The spellings that begin with a small letter. Only those can be
    damaged by the sentence capital, so only those need guarding."""
    return tuple(t for t in terms if t and t[0].islower())


def _capitalise(match: re.Match[str], keep: tuple[str, ...]) -> str:
    head, letter = match.group(1), match.group(2)
    rest = match.string[match.start(2):]
    for spelling in keep:
        if not rest.startswith(spelling):
            continue
        after = rest[len(spelling):len(spelling) + 1]
        if not after or not WORD_CHAR_RE.match(after):
            return head + letter        # a whole dictionary word: leave it
    return head + letter.upper()
