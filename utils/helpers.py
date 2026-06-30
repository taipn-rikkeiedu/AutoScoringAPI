import re


def parse_score(report_text: str) -> str | None:
    """Trích xuất tổng điểm số từ báo cáo Markdown dạng bảng."""
    match = re.search(r"(\d+)\s*/\s*100", report_text)
    if match:
        return match.group(1)
    match_fallback = re.search(
        r"(?:Tổng điểm|TỔNG|Score|Points):\s*\*?(\d+)\*?",
        report_text,
        re.IGNORECASE,
    )
    if match_fallback:
        return match_fallback.group(1)
    return None


def is_streamlit_running() -> bool:
    """Trả về False vì dự án này chỉ chạy API Backend FastAPI."""
    return False
