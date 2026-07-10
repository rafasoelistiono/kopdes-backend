import hashlib
import json
import threading
import time
from typing import Any


class TTLCache:
    def __init__(self, ttl: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl
        self._lock = threading.Lock()

    def _make_key(self, dashboard_key: str, params: dict) -> str:
        raw = json.dumps({"key": dashboard_key, "params": params}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, dashboard_key: str, params: dict) -> Any | None:
        key = self._make_key(dashboard_key, params)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            data, ts = entry
            if time.time() - ts > self._ttl:
                del self._store[key]
                return None
            return data

    def set(self, dashboard_key: str, params: dict, data: Any):
        key = self._make_key(dashboard_key, params)
        with self._lock:
            self._store[key] = (data, time.time())

    def clear(self):
        with self._lock:
            self._store.clear()

    def stats(self) -> dict:
        with self._lock:
            return {"entries": len(self._store), "ttl": self._ttl}


dashboard_cache = TTLCache(ttl=300)
