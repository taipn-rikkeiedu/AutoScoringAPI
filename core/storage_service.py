from core.settings import Settings


def load_templates():
    from core.exercise_service import ExerciseService

    return ExerciseService.load_templates()


def save_templates(templates):
    from core.exercise_service import ExerciseService

    return ExerciseService.save_templates(templates)


def get_ai_config():
    from core.sync_service import get_sync_paths
    import json
    import os

    # 1. Cấu hình mặc định từ class Settings
    config = {
        "provider": Settings.AI_PROVIDER or "gemini",
        "gemini_api_key": Settings.GEMINI_API_KEY,
        "gemini_model_name": Settings.DEFAULT_MODEL,
        "deepseek_api_key": Settings.DEEPSEEK_API_KEY,
        "deepseek_api_base_url": Settings.DEEPSEEK_API_BASE_URL,
        "deepseek_model_name": Settings.DEEPSEEK_MODEL_NAME,
        "openrouter_api_key": getattr(Settings, "OPENROUTER_API_KEY", ""),
        "openrouter_api_base_url": getattr(
            Settings, "OPENROUTER_API_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        "openrouter_model_name": getattr(
            Settings, "OPENROUTER_MODEL_NAME", "qwen/qwen3-coder:free"
        ),
        "custom_api_key": Settings.CUSTOM_API_KEY,
        "custom_api_base_url": Settings.CUSTOM_API_BASE_URL,
        "custom_model_name": Settings.CUSTOM_MODEL_NAME or Settings.DEFAULT_MODEL,
        "local_model_name": Settings.LOCAL_MODEL_NAME,
        "ollama_base_url": Settings.OLLAMA_BASE_URL,
        "github_token": Settings.GITHUB_TOKEN,
        "exercise_source": getattr(Settings, "EXERCISE_SOURCE", "local"),
        "exercise_api_url": getattr(Settings, "EXERCISE_API_URL", ""),
        "exercise_api_token": getattr(Settings, "EXERCISE_API_TOKEN", ""),
        "google_sheet_url": getattr(Settings, "GOOGLE_SHEET_URL", ""),
        "local_data_root": getattr(Settings, "LOCAL_DATA_ROOT", ""),
        "local_config_path": getattr(Settings, "LOCAL_CONFIG_PATH", ""),
        "local_templates_path": getattr(Settings, "LOCAL_TEMPLATES_PATH", ""),
        "local_sync_settings_path": getattr(Settings, "LOCAL_SYNC_SETTINGS_PATH", ""),
    }

    # 2. Ghi đè bằng tệp tin cấu hình cục bộ config.json
    paths = get_sync_paths()
    config_file = paths["config"]
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                if isinstance(config_data, dict):
                    config.update(config_data)
        except Exception:
            pass

    # 3. Tự động lấy cấu hình từ Streamlit Secrets nếu đang chạy trên Streamlit Cloud
    try:
        import streamlit as st
        if hasattr(st, "secrets") and st.secrets:
            if "ai_config" in st.secrets:
                for k, v in st.secrets["ai_config"].items():
                    config[k] = v
            for key in config.keys():
                if key in st.secrets:
                    config[key] = st.secrets[key]
                elif key.upper() in st.secrets:
                    config[key] = st.secrets[key.upper()]
    except Exception:
        pass

    # 4. Cập nhật động Settings class để các core service đọc đúng đường dẫn mới
    if config.get("local_data_root"):
        Settings.LOCAL_DATA_ROOT = config["local_data_root"]
    if config.get("local_config_path"):
        Settings.LOCAL_CONFIG_PATH = config["local_config_path"]
    if config.get("local_templates_path"):
        Settings.LOCAL_TEMPLATES_PATH = config["local_templates_path"]
    if config.get("local_sync_settings_path"):
        Settings.LOCAL_SYNC_SETTINGS_PATH = config["local_sync_settings_path"]

    return config


def provider_display_name(config: dict) -> str:
    provider = config.get("provider", "gemini")
    if provider == "local":
        model = config.get("local_model_name", Settings.LOCAL_MODEL_NAME)
        return f"Ollama Local ({model})"
    if provider == "custom":
        model = config.get("custom_model_name") or config.get("model_name", "custom")
        return f"Custom API ({model})"
    if provider == "deepseek":
        model = config.get("deepseek_model_name") or config.get(
            "model_name", Settings.DEEPSEEK_MODEL_NAME
        )
        return f"DeepSeek API ({model})"
    if provider == "openrouter":
        model = config.get("openrouter_model_name") or config.get(
            "model_name",
            getattr(Settings, "OPENROUTER_MODEL_NAME", "qwen/qwen3-coder:free"),
        )
        return f"OpenRouter ({model})"
    model = config.get("gemini_model_name") or config.get(
        "model_name", Settings.DEFAULT_MODEL
    )
    return f"Google Gemini ({model})"
