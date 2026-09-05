"""Your own words: names, jargon, and fixes for what the engine mishears.

Two mechanisms, because one alone is not enough.

  1. BIAS   - the term list is handed to the engine before it listens, so
              it leans toward producing your words. A nudge, not a promise.
              The list is deliberately kept short: long context makes these
              models drift and invent text on quiet audio.

  2. FIX    - a correction pass afterwards. Whole word, case insensitive,
              longest match first. This is the guaranteed path.

  3. CASE   - your terms are then re spelled your way, so "Claude code"
              becomes "Claude Code". Only for terms whose shape a
              sentence capital cannot explain, so plain words are safe.

The fix pass also catches words the engine glues together: an entry for
"Claude Code" matches "Claude Code", "Claude-Code" and "ClaudeCode".
Word boundaries stop it corrupting real words, so a rule for
"cloud code" can never touch "Cloudflare" or the plain word "cloud".
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import config

# The engine only reads a short hint, and a long one makes it drift.
MAX_BIAS_TERMS = 32
MAX_BIAS_CHARS = 380

STARTER = '''# Murmur reads this file every time it starts.
# You can edit it here or in the Dictionary tab. Both write the same file.

# 1) Words the engine should lean toward. Names, jargon, product names.
#    Keep this short - about 30 entries. A long list makes it drift.
terms = [
  "Murmur",
  "Anthropic",
  "Vercel",
  "Supabase",
]

# 2) Fixes applied after listening.  "when you hear X, write Y"
[corrections]
"cloud code" = "Claude Code"
"anthropic ai" = "Anthropic"
'''

# Ordinary words. A correction whose "heard" side is one of these would
# rewrite normal English, so we warn before it is saved.
COMMON_WORDS = {
    "a", "about", "after", "again", "all", "also", "and", "any", "are", "as",
    "at", "back", "be", "because", "been", "before", "being", "best", "better",
    "between", "big", "both", "but", "by", "call", "can", "case", "change",
    "check", "click", "close", "cloud", "code", "come", "could", "data", "day",
    "did", "do", "does", "done", "down", "each", "end", "even", "every", "far",
    "few", "file", "find", "first", "for", "from", "get", "give", "go", "good",
    "great", "group", "had", "has", "have", "he", "help", "her", "here", "him",
    "his", "home", "how", "i", "if", "in", "into", "is", "it", "its", "just",
    "keep", "key", "know", "large", "last", "left", "less", "let", "like",
    "line", "list", "little", "long", "look", "make", "man", "many", "may",
    "me", "mean", "might", "more", "most", "move", "much", "must", "my", "name",
    "need", "new", "next", "no", "not", "note", "now", "number", "of", "off",
    "old", "on", "one", "only", "open", "or", "order", "other", "our", "out",
    "over", "own", "page", "part", "people", "place", "point", "put", "read",
    "real", "right", "run", "said", "same", "say", "see", "set", "she",
    "should", "show", "side", "since", "small", "so", "some", "start", "state",
    "still", "such", "take", "team", "test", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "thing", "think", "this",
    "those", "through", "time", "to", "too", "top", "try", "turn", "two", "up",
    "us", "use", "used", "very", "want", "was", "way", "we", "well", "were",
    "what", "when", "where", "which", "while", "who", "why", "will", "with",
    "word", "work", "would", "write", "year", "you", "your",
}


def needs_case_help(term: str) -> bool:
    """Is this term's spelling something the model could not guess?

    Only terms whose shape cannot be explained by an ordinary capital at
    the start of a sentence. So "Claude Code", "PowerShell", "WSL" and
    "faster-whisper" are enforced, but a plain word like "Neon" is left
    alone. Rewriting every capital would damage ordinary English.
    """
    term = term.strip()
    if not term:
        return False
    if " " in term:                       # two words: "Claude Code"
        return True
    if not term.isalnum():                # a dot or a dash: "Next.js"
        return True
    if term.isupper() and len(term) > 1:  # all capitals: "WSL"
        return True
    # an inner capital: "PowerShell", "GitHub"
    return any(character.isupper() for character in term[1:])


@dataclass
class Applied:
    heard: str
    written: str
    count: int


@dataclass
class Risk:
    """A warning shown in the UI before an entry is saved."""

    level: str      # "warn" or "block"
    message: str


def dictionary_path() -> Path:
    return config.config_dir() / "dictionary.toml"


# One character that means "still inside a word": a letter or digit in any
# alphabet, the underscore, or a combining accent mark (the kind that sits
# on top of the letter before it). A match glued to one of these is only
# part of a longer word, so the rule must leave it alone.
#
# Decided on purpose:
#   underscore  = word character, so "my_cafe_var" is never touched
#   apostrophe  = boundary, so "cafe's" becomes "coffee's"
WORD_CHAR = (
    r"[\w"
    r"\u0300-\u036f"    # combining diacritical marks
    r"\u1ab0-\u1aff"    # ... extended
    r"\u1dc0-\u1dff"    # ... supplement
    r"\u20d0-\u20ff"    # ... for symbols
    r"\ufe20-\ufe2f"    # ... half marks
    r"]"
)
WORD_CHAR_RE = re.compile(WORD_CHAR)


def _pattern_for(heard: str) -> re.Pattern[str]:
    """Whole word, case insensitive, and tolerant of glue.

    The parts may be separated by spaces, hyphens, or nothing at all, so
    "Claude Code", "Claude-Code" and "ClaudeCode" all match. The lookarounds
    demand the whole pattern, which is what keeps "Cloudflare" safe. They
    understand every alphabet, so "cafe" never fires inside "cafeč".
    """
    parts = [re.escape(part) for part in heard.split() if part]
    if not parts:
        return re.compile(r"(?!x)x")  # matches nothing
    body = r"[\s\-_]*".join(parts)
    return re.compile(
        r"(?<!" + WORD_CHAR + ")" + body + r"(?!" + WORD_CHAR + ")",
        flags=re.IGNORECASE,
    )


def check_risk(heard: str, written: str) -> Risk | None:
    """Would this entry damage ordinary text? Called by the UI before saving."""
    heard = heard.strip()
    if not heard:
        return Risk("block", "Enter the words you hear.")
    if not written.strip():
        return Risk("block", "Enter what should be written instead.")

    words = heard.lower().split()
    joined = "".join(words)

    if len(words) == 1:
        if words[0] in COMMON_WORDS:
            return Risk(
                "warn",
                f'"{heard}" is an ordinary word. Every time you say it, it '
                f'will be replaced. Add a second word to make it specific.',
            )
        if len(joined) < 4:
            return Risk(
                "warn",
                f'"{heard}" is very short, so it will fire often. '
                f"Consider a longer phrase.",
            )

    if _pattern_for(heard).search(written) and heard.lower() != written.lower():
        return Risk(
            "warn",
            "What you write still contains what you hear, so this rule can "
            "fire again on its own output.",
        )
    return None


class Dictionary:
    def __init__(self, terms: list[str], corrections: dict[str, str]) -> None:
        self.terms = terms
        self.corrections = corrections
        self._recompile()

    # ---- loading and saving --------------------------------------------

    @classmethod
    def load(cls) -> "Dictionary":
        path = dictionary_path()
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(STARTER, encoding="utf-8")
            print(f"[dictionary] made a starter file at {path}")
        try:
            with path.open("rb") as handle:
                data = tomllib.load(handle)
        except Exception as error:
            print(f"[dictionary] could not read {path}: {error}")
            return cls([], {})

        terms = [str(t).strip() for t in data.get("terms", []) if str(t).strip()]
        corrections = {
            str(k).strip(): str(v).strip()
            for k, v in (data.get("corrections") or {}).items()
            if str(k).strip() and str(v).strip()
        }
        return cls(terms, corrections)

    def save(self) -> None:
        """Write the plain file back. Stays hand editable."""
        lines = [
            "# Murmur dictionary. Edit here or in the Dictionary tab.",
            "",
            "# 1) Words the engine should lean toward.",
            "terms = [",
        ]
        for term in self.terms:
            lines.append(f'  "{_escape(term)}",')
        lines += [
            "]",
            "",
            "# 2) Fixes applied after listening.",
            "[corrections]",
        ]
        for heard in sorted(self.corrections, key=str.lower):
            lines.append(f'"{_escape(heard)}" = "{_escape(self.corrections[heard])}"')
        lines.append("")

        path = dictionary_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text("\n".join(lines), encoding="utf-8")
        temp.replace(path)

    def _recompile(self) -> None:
        # Longest first, so "claude code cli" wins over "claude code".
        self._rules = [
            (heard, _pattern_for(heard), self.corrections[heard])
            for heard in sorted(self.corrections, key=lambda k: (-len(k), k.lower()))
        ]
        # MECHANISM 3: your terms, spelled your way. The engine often hears
        # the words but writes "Claude code". Longest first again.
        self._case_rules = [
            (_pattern_for(term), term)
            for term in sorted(self.terms, key=lambda t: (-len(t), t.lower()))
            if needs_case_help(term)
        ]

    # ---- editing --------------------------------------------------------

    def add_term(self, term: str) -> None:
        term = term.strip()
        if term and term.lower() not in {t.lower() for t in self.terms}:
            self.terms.append(term)
            self._recompile()
            self.save()

    def remove_term(self, term: str) -> None:
        self.terms = [t for t in self.terms if t.lower() != term.lower()]
        self._recompile()
        self.save()

    def set_correction(self, heard: str, written: str, replacing: str = "") -> None:
        if replacing and replacing in self.corrections:
            del self.corrections[replacing]
        self.corrections[heard.strip()] = written.strip()
        self._recompile()
        self.save()

    def remove_correction(self, heard: str) -> None:
        self.corrections.pop(heard, None)
        self._recompile()
        self.save()

    # ---- the two mechanisms ---------------------------------------------

    def bias_prompt(self) -> str:
        """A short hint handed to the engine BEFORE it listens."""
        if not self.terms:
            return ""
        chosen: list[str] = []
        length = 0
        for term in self.terms[:MAX_BIAS_TERMS]:
            if length + len(term) + 2 > MAX_BIAS_CHARS:
                break
            chosen.append(term)
            length += len(term) + 2
        if not chosen:
            return ""
        return ", ".join(chosen) + "."

    def spellings(self) -> list[str]:
        """Every spelling you asked for: your terms, plus whatever your
        corrections write. The cleanup pass must not undo any of these,
        so "iPhone" keeps its small i at the start of a sentence."""
        seen: set[str] = set()
        out: list[str] = []
        for word in [*self.terms, *self.corrections.values()]:
            if word and word not in seen:
                seen.add(word)
                out.append(word)
        return out

    def apply(self, text: str) -> tuple[str, list[Applied]]:
        """The correction pass AFTER listening. Returns the new text and
        a note of every rule that fired, so the history can show it."""
        # The replacement is handed over as a function, never as a string.
        # A string would be read as a regex template, and a value such as
        # C:\\Users\\... would crash on the "\\U".
        applied: list[Applied] = []
        for heard, pattern, written in self._rules:
            text, count = pattern.subn(lambda _m, value=written: value, text)
            if count:
                applied.append(Applied(heard=heard, written=written, count=count))

        for pattern, term in self._case_rules:
            fixed, count = pattern.subn(lambda _m, value=term: value, text)
            if count and fixed != text:
                applied.append(Applied(heard=term, written=term, count=count))
            text = fixed
        return text, applied

    def fix(self, text: str) -> str:
        """Same thing, when the caller does not care what fired."""
        return self.apply(text)[0]

    # kept so older code keeps working
    def prompt(self) -> str:
        return self.bias_prompt()


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
