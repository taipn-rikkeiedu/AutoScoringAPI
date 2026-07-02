import os
import json
from core.settings import Settings


def get_sync_paths():
    data_root = os.path.dirname(Settings.LOCAL_CONFIG_PATH)
    os.makedirs(data_root, exist_ok=True)
    return {
        "config": Settings.LOCAL_CONFIG_PATH,
        "templates": Settings.LOCAL_TEMPLATES_PATH,
        "sync_settings": Settings.LOCAL_SYNC_SETTINGS_PATH,
    }


def is_local_environment() -> bool:
    """Kiểm tra xem ứng dụng đang chạy ở môi trường máy cá nhân hay Streamlit Cloud."""
    if os.getenv("STREAMLIT_SHARING_ERC") or os.getenv("SHARING_USER_SERVER"):
        return False
    # Nếu đang chạy trong Docker container của Streamlit Cloud hoặc đường dẫn /app
    if os.path.exists("/app"):
        return False
    return True


def sync_config_to_disk(config: dict) -> None:
    """Đồng bộ cấu hình AI xuống ổ đĩa cục bộ (chỉ thực hiện khi chạy ở local)."""
    if not is_local_environment():
        return
    paths = get_sync_paths()
    config_file = paths["config"]
    try:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def sync_templates_to_disk(templates: dict) -> None:
    """Đồng bộ thư viện đề bài xuống ổ đĩa cục bộ (chỉ thực hiện khi chạy ở local)."""
    if not is_local_environment():
        return
    paths = get_sync_paths()
    templates_file = paths["templates"]
    try:
        os.makedirs(os.path.dirname(templates_file), exist_ok=True)
        with open(templates_file, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

