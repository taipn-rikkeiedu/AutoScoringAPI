import hashlib
import time
from core.settings import Settings

_GLOBAL_GRADING_CACHE: dict[str, dict] = {}


class CacheService:
    @staticmethod
    def make_cache_key(*parts: str) -> str:
        key = "|".join(part or "" for part in parts)
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @staticmethod
    def get_cached_result(key: str) -> dict | None:
        if not Settings.GRADING_CACHE_ENABLED:
            return None
        entry = _GLOBAL_GRADING_CACHE.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            _GLOBAL_GRADING_CACHE.pop(key, None)
            return None
        return entry["value"]

    @staticmethod
    def set_cached_result(key: str, value: dict) -> None:
        if not Settings.GRADING_CACHE_ENABLED:
            return
        expires_at = time.time() + Settings.GRADING_CACHE_TTL_MINUTES * 60
        _GLOBAL_GRADING_CACHE[key] = {"value": value, "expires_at": expires_at}
