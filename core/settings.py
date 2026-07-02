import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_VERSION = "1.0.0"
    LOCAL_DATA_ROOT = os.getenv("LOCAL_DATA_ROOT", "C:/AutoScoring" if os.name == "nt" else os.path.join(os.getcwd(), "data"))
    LOCAL_CONFIG_PATH = os.getenv(
        "LOCAL_CONFIG_PATH", os.path.join(LOCAL_DATA_ROOT, "config", "config.json")
    )
    LOCAL_TEMPLATES_PATH = os.getenv(
        "LOCAL_TEMPLATES_PATH", os.path.join(LOCAL_DATA_ROOT, "data", "templates.json")
    )
    LOCAL_SYNC_SETTINGS_PATH = os.getenv(
        "LOCAL_SYNC_SETTINGS_PATH", os.path.join(LOCAL_DATA_ROOT, ".sync_settings.json")
    )

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE_URL = os.getenv(
        "DEEPSEEK_API_BASE_URL", "https://api.deepseek.com"
    )
    DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_BASE_URL = os.getenv(
        "OPENROUTER_API_BASE_URL", "https://openrouter.ai/api/v1"
    )
    OPENROUTER_MODEL_NAME = os.getenv("OPENROUTER_MODEL_NAME", "qwen/qwen3-coder:free")
    OPENROUTER_MODELS = ["qwen/qwen3-coder:free", "deepseek/deepseek-r1:free", "google/gemini-2.5-pro:free"]
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-1.5-pro")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

    USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "False").lower() in (
        "true",
        "1",
        "yes",
    )
    LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "deepseek-r1:7b")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "")
    CUSTOM_API_BASE_URL = os.getenv("CUSTOM_API_BASE_URL", "")
    CUSTOM_MODEL_NAME = os.getenv("CUSTOM_MODEL_NAME", "")

    EXERCISE_SOURCE = os.getenv("EXERCISE_SOURCE", "local").strip().lower()
    EXERCISE_API_URL = os.getenv("EXERCISE_API_URL", "")
    EXERCISE_API_TOKEN = os.getenv("EXERCISE_API_TOKEN", "")
    GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "")

    ALLOWED_EXTENSIONS = (
        ".py",
        ".java",
        ".js",
        ".ts",
        ".cpp",
        ".c",
        ".cs",
        ".html",
        ".css",
        ".go",
        ".kt",
        ".php",
        ".gradle",
        ".xml",
        ".properties",
        ".yml",
        ".yaml",
        ".json",
        ".md",
        ".docx",
    )
    EXCLUDED_DIRS = (
        "node_modules/",
        ".venv",
        "env/",
        ".git/",
        "build/",
        "dist/",
        "target/",
        "__pycache/",
        ".idea/",
        ".vscode/",
    )
    EXCLUDED_FILES = (
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "composer.lock",
        "pom.xml.tag",
        ".gitignore",
        "LICENSE",
        "gradlew.bat",
        "gradlew",
        "mvnw.cmd",
        "mvnw",
    )

    GRADING_MAX_SCORE = int(os.getenv("GRADING_MAX_SCORE", "100"))
    GRADING_MAX_WORDS = int(os.getenv("GRADING_MAX_WORDS", "100"))
    GRADING_LANGUAGE = os.getenv("GRADING_LANGUAGE", "Tiếng Việt")
    MAX_PROJECT_FILES = int(os.getenv("MAX_PROJECT_FILES", "100"))
    MAX_PROJECT_CHARS = int(os.getenv("MAX_PROJECT_CHARS", "500000"))
    GRADING_CACHE_ENABLED = os.getenv("GRADING_CACHE_ENABLED", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    GRADING_CACHE_TTL_MINUTES = int(os.getenv("GRADING_CACHE_TTL_MINUTES", "120"))

    DEFAULT_CRITERIA = os.getenv(
        "DEFAULT_CRITERIA",
        "1. Đáp ứng yêu cầu nghiệp vụ của đề bài. (40 điểm)\n2. Logic xử lý chính xác và xử lý ngoại lệ tốt. (30 điểm)\n3. Cấu trúc mã nguồn sạch sẽ, dễ đọc, chuẩn hóa. (30 điểm)",
    )
    DEFAULT_TEMPLATES = {}

    @classmethod
    def validate(cls, provider=None, api_key=None, api_base_url=None):
        provider_name = (provider or cls.AI_PROVIDER or "gemini").strip().lower()
        if provider_name == "local":
            return
        if provider_name == "custom":
            if not (api_base_url or cls.CUSTOM_API_BASE_URL):
                raise ValueError("Thiếu CUSTOM_API_BASE_URL")
            if not (api_key or cls.CUSTOM_API_KEY):
                raise ValueError("Thiếu CUSTOM_API_KEY")
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
