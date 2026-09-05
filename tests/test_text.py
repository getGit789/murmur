"""Text pipeline checks: dictionary corrections and the rules cleaner.

Run from the repo root:   python -m unittest discover -s tests
No audio, no window, no key. Config is redirected to a temp folder.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from murmur import config  # noqa: E402

_TEMP = Path(tempfile.mkdtemp())
config.config_dir = lambda: _TEMP  # never touch %APPDATA%

from murmur.cleanup.rules import RulesCleaner  # noqa: E402
from murmur.dictionary import Dictionary  # noqa: E402

PATH = r"C:\Users\Damir\Murmur"


def make() -> Dictionary:
    return Dictionary(
        terms=["PowerShell", "eBay", "macOS", "Next.js", "Murmur"],
        corrections={
            "project folder": PATH,
            "cafe": "coffee",
            "cloud code": "Claude Code",
            "cloud code cli": "Claude Code CLI",
            "eye phone": "iPhone",
            "group ref": r"\1 and \g<name> cost $5 \"quoted\"",
        },
    )


class ReplacementIsLiteral(unittest.TestCase):
    def test_windows_path(self) -> None:
        text, applied = make().apply("open project folder now")
        self.assertEqual(text, f"open {PATH} now")
        self.assertEqual([(a.heard, a.count) for a in applied], [("project folder", 1)])

    def test_regex_looking_text_survives(self) -> None:
        text = make().fix("group ref")
        self.assertEqual(text, r"\1 and \g<name> cost $5 \"quoted\"")

    def test_term_with_backslash(self) -> None:
        d = Dictionary(terms=[r"C:\Tools"], corrections={})
        self.assertEqual(d.fix(r"see c:\tools"), r"see C:\Tools")

    def test_count_is_right(self) -> None:
        _, applied = make().apply("cafe cafe cafe")
        self.assertEqual(applied[0].count, 3)

    def test_path_survives_save_and_load(self) -> None:
        d = make()
        d.save()
        self.assertEqual(Dictionary.load().corrections["project folder"], PATH)


class WordBoundaries(unittest.TestCase):
    def test_standalone_word_changes(self) -> None:
        self.assertEqual(make().fix("a cafe here"), "a coffee here")

    def test_accented_letter_after(self) -> None:
        self.assertEqual(make().fix("cafeč"), "cafeč")

    def test_accented_letter_before(self) -> None:
        self.assertEqual(make().fix("čcafe"), "čcafe")

    def test_decomposed_accent_after(self) -> None:
        # "e" + combining acute = "é" written as two code points
        self.assertEqual(make().fix("cafe\u0301"), "cafe\u0301")

    def test_decomposed_accent_before(self) -> None:
        self.assertEqual(make().fix("c\u030ccafe"), "c\u030ccafe")

    def test_ascii_neighbours_are_safe(self) -> None:
        self.assertEqual(
            make().fix("Cloudflare cloudcodex cloud"), "Cloudflare cloudcodex cloud"
        )

    def test_glue_still_matches(self) -> None:
        d = make()
        self.assertEqual(d.fix("CloudCode"), "Claude Code")
        self.assertEqual(d.fix("Cloud-Code"), "Claude Code")
        self.assertEqual(d.fix("cloud_code"), "Claude Code")

    def test_longest_rule_wins(self) -> None:
        self.assertEqual(make().fix("cloud code cli"), "Claude Code CLI")

    def test_apostrophe_is_a_boundary(self) -> None:
        self.assertEqual(make().fix("the cafe's door"), "the coffee's door")

    def test_underscore_is_part_of_a_word(self) -> None:
        self.assertEqual(make().fix("my_cafe_var"), "my_cafe_var")


class RepeatedWords(unittest.TestCase):
    def test_kept_by_default(self) -> None:
        c = RulesCleaner()
        self.assertEqual(c.clean("I had had enough"), "I had had enough.")
        self.assertEqual(c.clean("It is very very good"), "It is very very good.")
        self.assertEqual(c.clean("What it is is unclear"), "What it is is unclear.")
        self.assertEqual(c.clean("no no no"), "No no no.")

    def test_removed_only_when_asked(self) -> None:
        c = RulesCleaner(remove_repeats=True)
        self.assertEqual(c.clean("the the cat"), "The cat.")

    def test_other_rules_still_run(self) -> None:
        c = RulesCleaner()
        self.assertEqual(c.clean("um hello  world"), "Hello world.")
        self.assertEqual(c.clean("hello new paragraph world"), "Hello\n\nWorld.")
        self.assertEqual(c.clean("hello , world"), "Hello, world.")


class DictionarySpellingSurvivesCleanup(unittest.TestCase):
    """The controller runs: dictionary.apply -> cleaner.clean(text, spellings)."""

    def run_pipeline(self, raw: str) -> str:
        d = make()
        text, _ = d.apply(raw)
        return RulesCleaner().clean(text, d.spellings())

    def test_correction_output_at_sentence_start(self) -> None:
        self.assertEqual(self.run_pipeline("eye phone works"), "iPhone works.")

    def test_after_full_stop_and_newline(self) -> None:
        self.assertEqual(
            self.run_pipeline("ok. eye phone works new line eye phone again"),
            "Ok. iPhone works\niPhone again.",
        )

    def test_terms_at_sentence_start(self) -> None:
        self.assertEqual(self.run_pipeline("ebay is up"), "eBay is up.")
        self.assertEqual(self.run_pipeline("macos is up"), "macOS is up.")
        self.assertEqual(self.run_pipeline("next.js is up"), "Next.js is up.")
        self.assertEqual(self.run_pipeline("powershell is up"), "PowerShell is up.")

    def test_ordinary_sentences_still_capitalised(self) -> None:
        self.assertEqual(self.run_pipeline("hello world"), "Hello world.")

    def test_only_whole_words_are_protected(self) -> None:
        # "iPhones" is not the dictionary word "iPhone", so it gets a capital.
        self.assertEqual(RulesCleaner().clean("iPhones", ["iPhone"]), "IPhones.")

    def test_claude_fallback_keeps_spelling(self) -> None:
        from murmur.cleanup.llm import ClaudeCleaner

        cleaner = ClaudeCleaner({"timeout_seconds": 0.01})

        class Broken:
            class beta:  # noqa: N801
                class messages:  # noqa: N801
                    @staticmethod
                    def create(**_kwargs):
                        raise RuntimeError("no network")

        cleaner._client = Broken()
        self.assertEqual(cleaner.clean("iPhone works", ["iPhone"]), "iPhone works.")


class TermEditsTakeEffectAtOnce(unittest.TestCase):
    def test_add_term(self) -> None:
        d = Dictionary([], {})
        d.add_term("PowerShell")
        self.assertEqual(d.fix("powershell"), "PowerShell")

    def test_remove_term(self) -> None:
        d = Dictionary(["PowerShell"], {})
        d.remove_term("PowerShell")
        self.assertEqual(d.fix("powershell"), "powershell")

    def test_longer_term_still_wins(self) -> None:
        d = Dictionary([], {})
        d.add_term("Claude Code")
        d.add_term("Claude Code CLI")
        self.assertEqual(d.fix("claude code cli"), "Claude Code CLI")


if __name__ == "__main__":
    unittest.main()
