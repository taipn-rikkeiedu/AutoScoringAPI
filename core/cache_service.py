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


def get_cached_report(assignment: str, criteria: str, project_content: str) -> str | None:
    """Trả về báo cáo từ cache nếu có."""
    key = CacheService.make_cache_key(assignment, criteria, project_content)
    res = CacheService.get_cached_result(key)
    if res and isinstance(res, dict):
        return res.get("report")
    return None


def save_cached_report(
    assignment: str, criteria: str, project_content: str, report: str
) -> None:
    """Lưu báo cáo vào cache."""
    key = CacheService.make_cache_key(assignment, criteria, project_content)
    value = {"report": report}
    CacheService.set_cached_result(key, value)


def get_cache_stats() -> dict:
    """Lấy số lượng cache hiện tại."""
    return {"total_entries": len(_GLOBAL_GRADING_CACHE)}


def clear_cache() -> None:
    """Xóa sạch cache."""
    _GLOBAL_GRADING_CACHE.clear()

