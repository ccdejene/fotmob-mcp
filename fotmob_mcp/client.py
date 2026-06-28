from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit

import requests


class FotMobUnavailable(RuntimeError):
    pass


class FotMobClient:
    def __init__(
        self,
        base_url: str | None = None,
        cache_dir: str | Path | None = None,
        cache_ttl_seconds: int | None = None,
        x_mas: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("FOTMOB_BASE_URL") or "https://www.fotmob.com").rstrip("/")
        self.cache_dir = Path(cache_dir or os.getenv("FOTMOB_CACHE_DIR") or ".cache/fotmob")
        self.cache_ttl_seconds = int(cache_ttl_seconds or os.getenv("FOTMOB_CACHE_TTL_SECONDS") or 21600)
        self.x_mas = x_mas or os.getenv("FOTMOB_X_MAS") or None
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 FotMobMcp/0.1",
        }
        if self.x_mas:
            headers["x-mas"] = self.x_mas
        return headers

    def get_json(self, path: str, params: dict[str, str]) -> Any:
        cache_path = self._cache_path(path, params)
        cached = self._read_cache(cache_path)
        if cached is not None:
            return cached

        url = self._build_url(path, params)
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            if not response.content:
                payload = {}
            else:
                payload = response.json()
        except Exception as exc:
            raise FotMobUnavailable("FotMob data could not be fetched.") from exc

        if payload in (None, ""):
            raise FotMobUnavailable("FotMob data could not be fetched.")

        cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def _build_url(self, path: str, params: dict[str, str]) -> str:
        query = urlencode(params)
        base = path if urlsplit(path).scheme in {"http", "https"} else f"{self.base_url}{path}"
        return f"{base}?{query}" if query else base

    def _cache_path(self, path: str, params: dict[str, str]) -> Path:
        key = hashlib.sha256(f"{path}?{urlencode(sorted(params.items()))}".encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.json"

    def _read_cache(self, cache_path: Path) -> Any | None:
        if not cache_path.exists():
            return None
        age = time.time() - cache_path.stat().st_mtime
        if age > self.cache_ttl_seconds:
            return None
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if payload not in (None, "") else None
