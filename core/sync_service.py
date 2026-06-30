import os
from core.settings import Settings


def get_sync_paths():
    data_root = os.path.dirname(Settings.LOCAL_CONFIG_PATH)
    os.makedirs(data_root, exist_ok=True)
    return {
        "config": Settings.LOCAL_CONFIG_PATH,
        "templates": Settings.LOCAL_TEMPLATES_PATH,
        "sync_settings": Settings.LOCAL_SYNC_SETTINGS_PATH,
    }
