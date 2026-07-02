import os
import json
import streamlit as st
from core.settings import Settings
from core.sync_service import (
    get_sync_paths,
    is_local_environment,
    sync_config_to_disk,
    sync_templates_to_disk,
)

def auto_sync_on_startup():
    """Run once on startup to read config and templates from local disk."""
    if st.session_state.get("sync_completed"):
        return

    # Default sync_completed flag to True even on Cloud so we don't keep trying
    st.session_state.sync_completed = True

    if not is_local_environment():
        st.session_state.sync_local_active = False
        return

    st.session_state.sync_local_active = True
    paths = get_sync_paths()
    config_file = paths["config"]
    templates_file = paths["templates"]

    sync_details = []

    # 1. Sync Config
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                if isinstance(config_data, dict) and "provider" in config_data:
                    # Sync state
                    st.session_state.ai_config = config_data
                    # Sync input widgets keys to avoid sync conflicts on load
                    st.session_state.settings_provider_select = config_data.get("provider", "gemini")
                    
                    old_api_key = config_data.get("api_key", "")
                    old_model_name = config_data.get("model_name", Settings.DEFAULT_MODEL)
                    old_api_base_url = config_data.get("api_base_url", "")
                    prov = config_data.get("provider", "gemini")
                    
                    st.session_state.settings_gemini_api_key = config_data.get(
                        "gemini_api_key", old_api_key if prov == "gemini" else ""
                    )
                    st.session_state.settings_gemini_model_select = config_data.get(
                        "gemini_model_name", old_model_name if prov == "gemini" else Settings.DEFAULT_MODEL
                    )
                    st.session_state.settings_deepseek_api_key = config_data.get(
                        "deepseek_api_key", old_api_key if prov == "deepseek" else ""
                    )
                    st.session_state.settings_deepseek_api_base_url = config_data.get(
                        "deepseek_api_base_url", Settings.DEEPSEEK_API_BASE_URL
                    )
                    st.session_state.settings_deepseek_model_name = config_data.get(
                        "deepseek_model_name", Settings.DEEPSEEK_MODEL_NAME
                    )
                    st.session_state.settings_openrouter_api_key = config_data.get(
                        "openrouter_api_key", old_api_key if prov == "openrouter" else ""
                    )
                    st.session_state.settings_openrouter_model_select = config_data.get(
                        "openrouter_model_name", old_model_name if prov == "openrouter" else Settings.OPENROUTER_MODEL_NAME
                    )
                    st.session_state.settings_openrouter_api_base_url = config_data.get(
                        "openrouter_api_base_url", Settings.OPENROUTER_API_BASE_URL
                    )
                    st.session_state.settings_custom_api_key = config_data.get(
                        "custom_api_key", old_api_key if prov == "custom" else ""
                    )
                    st.session_state.settings_custom_api_base_url = config_data.get(
                        "custom_api_base_url", old_api_base_url if prov == "custom" else ""
                    )
                    st.session_state.settings_custom_model_name = config_data.get(
                        "custom_model_name", old_model_name if prov == "custom" else Settings.DEFAULT_MODEL
                    )
                    st.session_state.settings_local_model_name = config_data.get("local_model_name", Settings.LOCAL_MODEL_NAME)
                    st.session_state.settings_ollama_base_url = config_data.get("ollama_base_url", Settings.OLLAMA_BASE_URL)
                    st.session_state.settings_github_token = config_data.get("github_token", "")
                    st.session_state.settings_exercise_source = config_data.get("exercise_source", getattr(Settings, "EXERCISE_SOURCE", "local"))
                    st.session_state.settings_exercise_api_url = config_data.get("exercise_api_url", getattr(Settings, "EXERCISE_API_URL", ""))
                    st.session_state.settings_exercise_api_token = config_data.get("exercise_api_token", getattr(Settings, "EXERCISE_API_TOKEN", ""))
                    st.session_state.settings_google_sheet_url = config_data.get("google_sheet_url", getattr(Settings, "GOOGLE_SHEET_URL", ""))
                    st.session_state.settings_local_data_root = config_data.get("local_data_root", Settings.LOCAL_DATA_ROOT)
                    st.session_state.settings_local_config_path = config_data.get("local_config_path", Settings.LOCAL_CONFIG_PATH)
                    st.session_state.settings_local_templates_path = config_data.get("local_templates_path", Settings.LOCAL_TEMPLATES_PATH)
                    sync_details.append("Cấu hình AI")
        except Exception as e:
            st.warning(f"Không thể đọc config.json từ local: {str(e)}")
    else:
        # Create default config.json
        from core.storage_service import get_ai_config
        default_config = get_ai_config()
        sync_config_to_disk(default_config)
        sync_details.append("Cấu hình AI (tạo mới)")

    # 2. Sync Templates
    if os.path.exists(templates_file):
        try:
            with open(templates_file, "r", encoding="utf-8") as f:
                templates_data = json.load(f)
                if isinstance(templates_data, dict):
                    st.session_state.cloud_templates = templates_data
                    sync_details.append("Thư viện mẫu bài tập")
        except Exception as e:
            st.warning(f"Không thể đọc templates.json từ local: {str(e)}")
    else:
        # Create default templates.json
        from core.storage_service import load_templates
        default_templates = load_templates()
        sync_templates_to_disk(default_templates)
        sync_details.append("Mẫu bài tập (tạo mới)")

    if sync_details:
        st.session_state.sync_status_msg = f"Đã đồng bộ thành công: {', '.join(sync_details)} từ máy tính."
