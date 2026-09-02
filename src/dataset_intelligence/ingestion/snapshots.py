"""Credential-free local storage for permitted raw source snapshots."""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class SourceSnapshot:
    source_name: str
    source_url: str
    observed_at: str
    adapter_version: str
    response_identifier: str | None
    payload: dict[str, Any]

class SnapshotStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory; self.directory.mkdir(parents=True, exist_ok=True)
    def _path(self, source_name: str, source_url: str) -> Path:
        key = hashlib.sha256(f"{source_name}\x1f{source_url}".encode()).hexdigest()
        return self.directory / f"{key}.json"
    def put(self, snapshot: SourceSnapshot) -> None:
        self._path(snapshot.source_name, snapshot.source_url).write_text(json.dumps(snapshot.__dict__, sort_keys=True) + "\n")
    def get(self, source_name: str, source_url: str) -> SourceSnapshot | None:
        path = self._path(source_name, source_url)
        return SourceSnapshot(**json.loads(path.read_text())) if path.is_file() else None
