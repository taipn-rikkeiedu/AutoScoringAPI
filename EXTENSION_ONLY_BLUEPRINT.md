# Bản thiết kế dự án: AI GitHub Grader (Chỉ lấy phần Extension + API Backend) 📐

Tài liệu này đóng vai trò như một **bản thiết kế (blueprint)** giúp bạn tạo một dự án mới hoàn toàn từ đầu, chỉ giữ lại phần **Chrome/Edge Extension** và **API Backend (FastAPI)**, loại bỏ hoàn toàn mã nguồn liên quan đến Streamlit.

---

## 📁 1. Cấu trúc thư mục dự án mới

Hãy tạo cấu trúc thư mục như sau trong dự án mới của bạn:

```text
ai-github-grader-extension/
├── requirements.txt
├── .env
├── api.py                # Entrypoint khởi chạy API
├── core/                 # Thư mục xử lý logic lõi (Python package)
│   ├── __init__.py
│   ├── settings.py       # Cấu hình hệ thống & biến môi trường
│   ├── github_service.py # Logic kết nối GitHub tải mã nguồn
│   ├── ai_service.py     # Logic prompt và kết nối nhà cung cấp AI
│   ├── cache_service.py  # Bộ nhớ đệm lưu kết quả đánh giá offline
│   ├── exercise_service.py # Quản lý nạp bài tập (Local JSON hoặc REST API)
│   ├── storage_service.py # Phụ trợ lưu trữ cấu hình
│   └── sync_service.py   # Phụ trợ ghi dữ liệu xuống đĩa cục bộ
├── extension/            # Thư mục chứa tiện ích mở rộng trình duyệt
│   ├── manifest.json     # Cấu hình Extension (Manifest V3)
│   ├── popup.html        # Giao diện người dùng của Extension
│   ├── popup.js          # Logic bắt URL GitHub & gọi API Backend
│   ├── marked.min.js     # Thư viện phân tích Markdown (để hiển thị báo cáo đẹp)
│   ├── icon.png          # Biểu tượng của Extension (128x128)
│   └── api_server.py     # FastAPI Server logic
└── utils/                # Thư mục tiện ích dùng chung
    ├── __init__.py
    └── helpers.py        # Các hàm helper (is_streamlit_running, parse_score)
```

---

## 📄 2. Nội dung chi tiết các tệp tin

### 1. `requirements.txt`
```text
fastapi
uvicorn
requests
python-dotenv
google-generativeai
httpx2
```

### 2. `api.py` (Entrypoint gốc)
```python
import uvicorn
import os

if __name__ == "__main__":
    # Đọc PORT từ môi trường (hỗ trợ Deploy Cloud) hoặc chạy mặc định cổng 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("extension.api_server:app", host="0.0.0.0", port=port, reload=True)
```

### 3. `core/settings.py`
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_VERSION = "1.0.0"
    LOCAL_DATA_ROOT = "C:/AutoScoring"
    LOCAL_CONFIG_PATH = "C:/AutoScoring/config/config.json"
    LOCAL_TEMPLATES_PATH = "C:/AutoScoring/data/templates.json"
    LOCAL_SYNC_SETTINGS_PATH = "C:/AutoScoring/.sync_settings.json"
    
    # AI Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE_URL = os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_BASE_URL = os.getenv("OPENROUTER_API_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL_NAME = os.getenv("OPENROUTER_MODEL_NAME", "qwen/qwen3-coder:free")
    
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-1.5-pro")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    
    # Local Ollama AI Settings
    USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "False").lower() in ("true", "1", "yes")
    LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "deepseek-r1:7b")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Custom API
    CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "")
    CUSTOM_API_BASE_URL = os.getenv("CUSTOM_API_BASE_URL", "")
    CUSTOM_MODEL_NAME = os.getenv("CUSTOM_MODEL_NAME", "")
    
    # Nguồn bài tập mặc định
    EXERCISE_SOURCE = os.getenv("EXERCISE_SOURCE", "local").strip().lower()
    EXERCISE_API_URL = os.getenv("EXERCISE_API_URL", "")
    EXERCISE_API_TOKEN = os.getenv("EXERCISE_API_TOKEN", "")
    
    # Rules
    ALLOWED_EXTENSIONS = (".py", ".java", ".js", ".ts", ".cpp", ".c", ".cs", ".html", ".css", ".go", ".kt", ".php", ".gradle", ".xml", ".properties", ".yml", ".yaml", ".json", ".md", ".docx")
    EXCLUDED_DIRS = ("node_modules/", ".venv", "env/", ".git/", "build/", "dist/", "target/", "__pycache__/", ".idea/", ".vscode/")
    EXCLUDED_FILES = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "composer.lock", "pom.xml.tag", ".gitignore", "LICENSE", "gradlew.bat", "gradlew", "mvnw.cmd", "mvnw")
    
    GRADING_MAX_SCORE = int(os.getenv("GRADING_MAX_SCORE", "100"))
    GRADING_MAX_WORDS = int(os.getenv("GRADING_MAX_WORDS", "100"))
    GRADING_LANGUAGE = os.getenv("GRADING_LANGUAGE", "Tiếng Việt")
    MAX_PROJECT_FILES = int(os.getenv("MAX_PROJECT_FILES", "100"))
    MAX_PROJECT_CHARS = int(os.getenv("MAX_PROJECT_CHARS", "500000"))
    GRADING_CACHE_ENABLED = os.getenv("GRADING_CACHE_ENABLED", "True").lower() in ("true", "1", "yes")
    GRADING_CACHE_TTL_MINUTES = int(os.getenv("GRADING_CACHE_TTL_MINUTES", "120"))
    
    DEFAULT_CRITERIA = "1. Đáp ứng yêu cầu nghiệp vụ của đề bài. (40 điểm)\n2. Logic xử lý chính xác và xử lý ngoại lệ tốt. (30 điểm)\n3. Cấu trúc mã nguồn sạch sẽ, dễ đọc, chuẩn hóa. (30 điểm)"
    DEFAULT_TEMPLATES = {}

    @classmethod
    def validate(cls, provider=None, api_key=None, api_base_url=None):
        provider_name = (provider or cls.AI_PROVIDER or "gemini").strip().lower()
        if provider_name == "local": return
        if provider_name == "custom":
            if not (api_base_url or cls.CUSTOM_API_BASE_URL):
                raise ValueError("Thiếu CUSTOM_API_BASE_URL")
            return
        if provider_name == "deepseek":
            if not (api_key or cls.DEEPSEEK_API_KEY):
                raise ValueError("Thiếu DEEPSEEK_API_KEY")
            return
        if provider_name == "openrouter":
            if not (api_key or cls.OPENROUTER_API_KEY):
                raise ValueError("Thiếu OPENROUTER_API_KEY")
            return
        if not (api_key or cls.GEMINI_API_KEY):
            raise ValueError("Thiếu GEMINI_API_KEY")
```

### 4. `core/github_service.py`
*(Copy nội dung từ file hiện tại của dự án: [github_service.py](file:///s:/WorkSpace/AutoScoring/core/github_service.py). Đảm bảo imports đã được trỏ sang `from core.settings import Settings` và `from core.storage_service import get_ai_config`)*

### 5. `core/ai_service.py`
*(Copy nội dung từ file hiện tại của dự án: [ai_service.py](file:///s:/WorkSpace/AutoScoring/core/ai_service.py). Đảm bảo import Settings trỏ về `from core.settings import Settings`)*

### 6. `core/cache_service.py`
*(Copy nội dung từ file hiện tại của dự án: [cache_service.py](file:///s:/WorkSpace/AutoScoring/core/cache_service.py). Tệp này đã được tối ưu hóa bằng `_GLOBAL_GRADING_CACHE` khi chạy ở môi trường không Streamlit).*

### 7. `core/exercise_service.py`
*(Copy nội dung từ file hiện tại của dự án: [exercise_service.py](file:///s:/WorkSpace/AutoScoring/core/exercise_service.py). Hỗ trợ nạp bài tập từ file JSON nội bộ hoặc tải trực tuyến thông qua REST API).*

### 8. `core/storage_service.py`
```python
from core.settings import Settings

def load_templates():
    from core.exercise_service import ExerciseService
    return ExerciseService.load_templates()

def save_templates(templates):
    from core.exercise_service import ExerciseService
    return ExerciseService.save_templates(templates)

def get_ai_config():
    # Khi chạy API Backend độc lập (không có Streamlit Session State)
    # Hàm này sẽ nạp trực tiếp cấu hình từ file config.json trên đĩa (nếu có)
    from core.sync_service import get_sync_paths
    import os
    import json
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
        "openrouter_api_base_url": getattr(Settings, "OPENROUTER_API_BASE_URL", "https://openrouter.ai/api/v1"),
        "openrouter_model_name": getattr(Settings, "OPENROUTER_MODEL_NAME", "qwen/qwen3-coder:free"),
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
        model = config.get("deepseek_model_name") or config.get("model_name", Settings.DEEPSEEK_MODEL_NAME)
        return f"DeepSeek API ({model})"
    if provider == "openrouter":
        model = config.get("openrouter_model_name") or config.get("model_name", getattr(Settings, "OPENROUTER_MODEL_NAME", "qwen/qwen3-coder:free"))
        return f"OpenRouter ({model})"
    model = config.get("gemini_model_name") or config.get("model_name", Settings.DEFAULT_MODEL)
    return f"Google Gemini ({model})"
```

### 9. `core/sync_service.py`
*(Copy nội dung từ file hiện tại của dự án: [sync_service.py](file:///s:/WorkSpace/AutoScoring/core/sync_service.py). File này đã được loại bỏ hàm `auto_sync_on_startup` phụ thuộc Streamlit).*

### 10. `utils/helpers.py`
```python
import re

def parse_score(report_text: str) -> str | None:
    """Trích xuất tổng điểm số từ báo cáo Markdown dạng bảng."""
    match = re.search(r'(\d+)\s*/\s*100', report_text)
    if match:
        return match.group(1)
    match_fallback = re.search(
        r'(?:Tổng điểm|TỔNG|Score|Points):\s*\*?(\d+)\*?',
        report_text,
        re.IGNORECASE,
    )
    if match_fallback:
        return match_fallback.group(1)
    return None

def is_streamlit_running() -> bool:
    """Trả về False vì dự án này chỉ chạy API Backend FastAPI."""
    return False
```

### 11. `extension/api_server.py`
*(Copy nội dung từ file hiện tại của dự án: [api_server.py](file:///s:/WorkSpace/AutoScoring/extension/api_server.py).)*

### 12. `extension/manifest.json`
*(Copy nội dung từ file hiện tại của dự án: [manifest.json](file:///s:/WorkSpace/AutoScoring/extension/manifest.json).)*

### 13. `extension/popup.html`
*(Copy nội dung từ file hiện tại của dự án: [popup.html](file:///s:/WorkSpace/AutoScoring/extension/popup.html).)*

### 14. `extension/popup.js`
*(Copy nội dung từ file hiện tại của dự án: [popup.js](file:///s:/WorkSpace/AutoScoring/extension/popup.js).)*

---

## 🚀 3. Hướng dẫn chạy nhanh dự án mới

1.  **Cài đặt môi trường & Thư viện**:
    ```bash
    python -m venv .venv
    # Kích hoạt venv (Xem hướng dẫn kích hoạt venv tại Hướng dẫn SETUP_EXTENSION.md)
    pip install -r requirements.txt
    ```
2.  **Khởi động API Server**:
    ```bash
    python api.py
    ```
3.  **Tải tiện ích Extension lên Chrome/Edge**:
    *   Mở trang quản lý Extension của trình duyệt (`chrome://extensions/` hoặc `edge://extensions/`).
    *   Bật **Chế độ nhà phát triển (Developer mode)**.
    *   Chọn **Tải tiện ích đã giải nén (Load unpacked)** và trỏ tới thư mục `extension/`.
