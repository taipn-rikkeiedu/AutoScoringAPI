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

    paths = get_sync_paths()
    config_file = paths["config"]
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                if isinstance(config_data, dict) and "provider" in config_data:
                    return config_data
        except Exception:
            pass

    return {
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
    }


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
