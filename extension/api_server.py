import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.github_service import GithubService, GitHubService
from core.ai_service import AIService
from core.cache_service import CacheService, get_cached_report, save_cached_report
from core.storage_service import get_ai_config, provider_display_name
from core.exercise_service import ExerciseService

app = FastAPI(title="AI GitHub Grader API")
service = AIService()

# Tích hợp cấu hình CORS Middleware để cho phép Extension kết nối từ bất kỳ origin nào
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GradeRequest(BaseModel):
    github_url: str
    provider: str | None = None
    api_key: str | None = None
    api_base_url: str | None = None
    model_name: str | None = None
    criteria: str | None = None


class GradeResponse(BaseModel):
    provider: str
    provider_display_name: str
    model: str
    score: str
    report: str
    prompt: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/grade", response_model=GradeResponse)
def grade_project(request: GradeRequest):
    try:
        files = GithubService.fetch_repo_files(request.github_url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Tạo khóa băm nâng cao: Đề bài/Tiêu chí + Nội dung toàn bộ mã nguồn dự án
    project_content_str = "".join([f.get("content", "") for f in files])
    criteria_str = request.criteria or ""
    
    cache_key = CacheService.make_cache_key(
        request.github_url,
        project_content_str,
        criteria_str,
        request.provider or "",
        request.model_name or "",
        request.api_base_url or "",
    )
    
    cached = CacheService.get_cached_result(cache_key)
    if cached:
        return cached

    try:
        result = service.grade_project(
            request.github_url,
            files,
            provider=request.provider,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name,
            criteria=request.criteria,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    response = {
        "provider": result["provider"],
        "provider_display_name": provider_display_name(get_ai_config()),
        "model": result["model"],
        "score": result["score"],
        "report": result["report"],
        "prompt": result["prompt"],
    }
    CacheService.set_cached_result(cache_key, response)
    return response


@app.post("/config")
def save_config(payload: dict):
    from core.sync_service import get_sync_paths
    import json

    paths = get_sync_paths()
    config_file = paths["config"]
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"status": "saved"}


@app.get("/config")
def load_config():
    from core.sync_service import get_sync_paths
    import json

    paths = get_sync_paths()
    config_file = paths["config"]
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return get_ai_config()


@app.get("/exercises")
def get_exercises():
    try:
        templates = ExerciseService.load_templates()
        return templates
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/parse-docx")
async def parse_docx(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ tệp tin định dạng .docx")
    try:
        contents = await file.read()
        text = GithubService.extract_docx_text(contents)
        if text.startswith("[Lỗi"):
            raise ValueError(text)
        return {"text": text}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── API endpoints for unittest and client ──

class ApiGradeRequest(BaseModel):
    repo_url: str
    chapter: str
    session: str
    assignment_name: str


@app.get("/api/config")
def api_get_config():
    config = get_ai_config()
    return {
        "provider": config.get("provider", "gemini"),
        "exercise_source": config.get("exercise_source", "local"),
        "has_github_token": bool(config.get("github_token")),
    }


@app.get("/api/exercises")
def api_get_exercises():
    try:
        return ExerciseService.load_templates()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/grade")
def api_grade_project(request: ApiGradeRequest):
    try:
        templates = ExerciseService.load_templates()
        chapter_data = templates.get(request.chapter, {})
        session_data = chapter_data.get(request.session, {})
        assignment_data = session_data.get(request.assignment_name, {})
        
        if not assignment_data:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")
            
        assignment_text = assignment_data.get("assignment", "")
        criteria_text = assignment_data.get("criteria", "")
        
        # Lấy nội dung repository qua GitHubService
        repo_data = GitHubService.get_repo_contents(request.repo_url)
        content_str = repo_data["content"]
        total_files = repo_data["total_files"]
        
        # Kiểm tra cache
        cached_report = get_cached_report(assignment_text, criteria_text, content_str)
        cache_hit = False
        
        if cached_report:
            report_text = cached_report
            cache_hit = True
        else:
            ai_service = AIService()
            prompt = ai_service.build_prompt_from_strings(assignment_text, criteria_text, content_str)
            config = get_ai_config()
            provider = (config.get("provider") or "gemini").strip().lower()
            model = ai_service.resolve_model_name(provider, config)
            api_key = ai_service.resolve_api_key(provider, config)
            api_base_url = (
                config.get("custom_api_base_url")
                or config.get("openrouter_api_base_url")
                or "https://openrouter.ai/api/v1"
            )
            report_text = ai_service.send_to_model(provider, api_key, api_base_url, model, prompt)
            save_cached_report(assignment_text, criteria_text, content_str, report_text)
            
        from utils.helpers import parse_score
        score = parse_score(report_text) or "N/A"
        
        return {
            "success": True,
            "cache_hit": cache_hit,
            "score": score,
            "total_files": total_files,
            "report": report_text
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

