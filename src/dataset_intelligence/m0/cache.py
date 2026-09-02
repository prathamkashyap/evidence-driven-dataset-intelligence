"""Filesystem cache for permitted M0 HTTP responses, with no credentials."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CachedResponse:
    body: bytes
    status_code: int | None
    error_kind: str | None
    fetched_at: str


class ResponseCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def get(self, url: str) -> CachedResponse | None:
        path = self.directory / f"{self.key(url)}.json"
        if not path.is_file():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        return CachedResponse(
            body=base64.b64decode(value["body_base64"]), status_code=value["status_code"],
            error_kind=value["error_kind"], fetched_at=value["fetched_at"],
        )

    def put(self, url: str, response: CachedResponse) -> None:
        value = {
            "url": url, "status_code": response.status_code, "error_kind": response.error_kind,
            "fetched_at": response.fetched_at,
            "body_base64": base64.b64encode(response.body).decode("ascii"),
        }
        (self.directory / f"{self.key(url)}.json").write_text(
            json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )

    def clear(self) -> None:
        for path in self.directory.glob("*.json"):
            path.unlink()
