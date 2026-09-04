"""Every transcript, kept on disk so the window can show it again.

One JSON object per line. Easy to read, easy to append, hard to corrupt.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from . import config

MAX_ENTRIES = 2000


@dataclass
class Applied:
    """One correction that fired."""

    heard: str
    written: str
    count: int


@dataclass
class Entry:
    raw: str                       # what the engine produced
    final: str                     # what actually got typed
    seconds: float
    engine: str
    corrections: list[Applied] = field(default_factory=list)
    at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @property
    def when(self) -> datetime:
        try:
            return datetime.fromisoformat(self.at)
        except ValueError:
            return datetime.now()

    @property
    def was_corrected(self) -> bool:
        return bool(self.corrections)


def history_path() -> Path:
    return config.config_dir() / "history.jsonl"


class History:
    """Reads the whole file once, then keeps it in memory."""

    def __init__(self) -> None:
        self.entries: list[Entry] = []
        self.load()

    def load(self) -> None:
        path = history_path()
        self.entries = []
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                data["corrections"] = [Applied(**c) for c in data.get("corrections", [])]
                self.entries.append(Entry(**data))
            except Exception:
                continue  # a bad line should never stop the app starting
        self.entries.sort(key=lambda e: e.at, reverse=True)

    def add(self, entry: Entry) -> Entry:
        self.entries.insert(0, entry)
        path = history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        if len(self.entries) > MAX_ENTRIES:
            self.entries = self.entries[:MAX_ENTRIES]
            self._rewrite()
        return entry

    def update(self, entry_id: str, final: str) -> None:
        """A manual fix to one transcript, kept on disk."""
        for entry in self.entries:
            if entry.id == entry_id:
                entry.final = final
                self._rewrite()
                return

    def delete(self, entry_id: str) -> None:
        self.entries = [e for e in self.entries if e.id != entry_id]
        self._rewrite()

    def clear(self) -> None:
        self.entries = []
        self._rewrite()

    def search(self, query: str) -> list[Entry]:
        query = query.strip().lower()
        if not query:
            return list(self.entries)
        return [
            e
            for e in self.entries
            if query in e.final.lower() or query in e.raw.lower()
        ]

    def _rewrite(self) -> None:
        path = history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            for entry in reversed(self.entries):
                handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        temp.replace(path)
