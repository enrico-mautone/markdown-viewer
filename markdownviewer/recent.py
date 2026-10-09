import json
import logging
import os
from pathlib import Path

RECENT_LIMIT = 10

logger = logging.getLogger(__name__)


def default_recent_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / "MarkdownViewer" / "recent.json"


class RecentFiles:
    """The last RECENT_LIMIT opened files, newest first, persisted as JSON.

    Reopening a file moves it to the top; once the list is full the oldest
    entry drops out. Failing to read or write the state file never raises:
    the viewer must keep working, so the list just stays in memory.
    """

    def __init__(self, storage_path: Path):
        self._storage_path = storage_path
        self._paths = self._load()

    @property
    def paths(self) -> list[Path]:
        return list(self._paths)

    def add(self, path: Path) -> None:
        others = [p for p in self._paths if p != path]
        self._paths = [path, *others][:RECENT_LIMIT]
        self._save()

    def remove(self, path: Path) -> None:
        remaining = [p for p in self._paths if p != path]
        if len(remaining) == len(self._paths):
            return
        self._paths = remaining
        self._save()

    def clear(self) -> None:
        self._paths = []
        self._save()

    def _load(self) -> list[Path]:
        try:
            data = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except (OSError, ValueError) as exc:
            logger.warning("Ignoring unreadable recent files list %s: %s", self._storage_path, exc)
            return []
        entries = data.get("files") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            return []
        valid = [Path(entry) for entry in entries if isinstance(entry, str) and entry]
        return valid[:RECENT_LIMIT]

    def _save(self) -> None:
        payload = json.dumps({"files": [str(p) for p in self._paths]}, indent=2)
        temp_path = self._storage_path.with_suffix(".json.tmp")
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_text(payload, encoding="utf-8")
            os.replace(temp_path, self._storage_path)
        except OSError as exc:
            logger.warning("Could not save recent files list to %s: %s", self._storage_path, exc)
