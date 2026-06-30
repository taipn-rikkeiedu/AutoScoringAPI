import os
import re
import requests
import io
import zipfile
import xml.etree.ElementTree as ET
from typing import List
from core.settings import Settings


class GithubService:
    API_BASE = "https://api.github.com"
    RAW_BASE = "https://raw.githubusercontent.com"

    @staticmethod
    def parse_github_url(url: str) -> dict:
        pattern = (
            r"https?://github\.com/([^/]+)/([^/]+)(?:/(tree|blob)/([^/]+)(?:/(.*))?)?"
        )
        match = re.match(pattern, url)
        if not match:
            raise ValueError("URL GitHub không hợp lệ")
        owner, repo, _, branch, rest = match.groups()
        repo = repo.rstrip(".git")
        return {
            "owner": owner,
            "repo": repo,
            "branch": branch or "main",
            "path": rest or "",
        }

    @classmethod
    def get_headers(cls) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ai-github-grader",
        }
        if Settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {Settings.GITHUB_TOKEN}"
        return headers

    @classmethod
    def extract_docx_text(cls, docx_bytes: bytes) -> str:
        """Trích xuất văn bản thô từ tệp .docx trong bộ nhớ."""
        try:
            with zipfile.ZipFile(io.BytesIO(docx_bytes)) as doc_zip:
                if "word/document.xml" in doc_zip.namelist():
                    xml_content = doc_zip.read("word/document.xml")
                    root = ET.fromstring(xml_content)
                    texts = []
                    for elem in root.iter():
                        # Lấy nội dung text trong các thẻ <w:t>
                        if elem.tag.endswith("}t") and elem.text:
                            texts.append(elem.text)
                    return " ".join(texts)
        except Exception as e:
            return f"[Lỗi trích xuất tài liệu .docx: {str(e)}]"
        return ""

    @classmethod
    def fetch_repo_files(
        cls, github_url: str, max_files: int | None = None
    ) -> List[dict]:
        info = cls.parse_github_url(github_url)
        owner = info["owner"]
        repo = info["repo"]
        branch = info["branch"]
        target_path = info["path"]
        max_files = max_files or Settings.MAX_PROJECT_FILES
        max_chars = Settings.MAX_PROJECT_CHARS

        # Thử tải toàn bộ repo bằng ZIP Archive (Fastest Path)
        branches_to_try = [branch]
        if branch not in ("main", "master"):
            branches_to_try.extend(["main", "master"])

        zip_success = False
        files = []

        for b in branches_to_try:
            zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{b}"
            try:
                response = requests.get(zip_url, headers=cls.get_headers(), timeout=30)
                if response.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        namelist = z.namelist()
                        if not namelist:
                            continue
                        
                        # Thư mục gốc do GitHub tự chèn: "repo-branch/"
                        prefix = namelist[0].split('/')[0] + '/'
                        
                        count = 0
                        total_len = 0
                        
                        for name in namelist:
                            cleaned_path = name[len(prefix):] if name.startswith(prefix) else name
                            
                            if target_path and not cleaned_path.startswith(target_path):
                                continue
                                
                            if name.endswith('/') or cls.is_excluded_path(cleaned_path):
                                continue
                                
                            if cls.has_allowed_extension(cleaned_path):
                                file_bytes = z.read(name)
                                _, ext = os.path.splitext(cleaned_path.lower())
                                
                                if ext == ".docx":
                                    content = cls.extract_docx_text(file_bytes)
                                else:
                                    try:
                                        content = file_bytes.decode("utf-8")
                                    except UnicodeDecodeError:
                                        try:
                                            content = file_bytes.decode("latin-1")
                                        except Exception:
                                            continue
                                
                                files.append({"path": cleaned_path, "content": content})
                                total_len += len(content)
                                count += 1
                                
                                if count >= max_files or total_len >= max_chars:
                                    break
                                    
                        if files:
                            zip_success = True
                            break
            except Exception:
                pass

        if zip_success:
            return files

        # --- FALLBACK 1: Git Trees API ---
        try:
            tree_url = f"{cls.API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            response = requests.get(tree_url, headers=cls.get_headers(), timeout=30)
            if response.status_code == 200:
                items = response.json().get("tree", [])
                allowed = []
                for item in items:
                    if item.get("type") != "blob":
                        continue
                    path = item.get("path", "")
                    if target_path and not path.startswith(target_path):
                        continue
                    if cls.is_excluded_path(path):
                        continue
                    if cls.has_allowed_extension(path):
                        allowed.append(path)
                        if len(allowed) >= max_files:
                            break

                for path in allowed:
                    content = cls.fetch_raw_file(owner, repo, branch, path)
                    if content is not None:
                        files.append({"path": path, "content": content})
                if files:
                    return files
        except Exception:
            pass

        # --- FALLBACK 2: Contents API & Tải đệ quy cơ bản ---
        try:
            files = cls.fetch_via_contents_api(owner, repo, branch, target_path, max_files)
            if files:
                return files
        except Exception as e:
            raise ValueError(f"Không thể đọc repository GitHub bằng bất kỳ phương thức nào: {str(e)}")

        if not files:
            raise ValueError("Không tìm thấy tệp nguồn hợp lệ trong repo GitHub")
        return files

    @classmethod
    def fetch_via_contents_api(
        cls, owner: str, repo: str, branch: str, path: str, max_files: int, current_files: List[dict] = None
    ) -> List[dict]:
        if current_files is None:
            current_files = []
        if len(current_files) >= max_files:
            return current_files

        url = f"{cls.API_BASE}/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        response = requests.get(url, headers=cls.get_headers(), timeout=30)
        if response.status_code != 200:
            return current_files

        items = response.json()
        if not isinstance(items, list):
            items = [items]

        for item in items:
            if len(current_files) >= max_files:
                break
            
            item_path = item.get("path", "")
            if item.get("type") == "dir":
                if not cls.is_excluded_path(item_path):
                    cls.fetch_via_contents_api(owner, repo, branch, item_path, max_files, current_files)
            elif item.get("type") == "file":
                if cls.is_excluded_path(item_path) or not cls.has_allowed_extension(item_path):
                    continue
                
                download_url = item.get("download_url")
                content = None
                if download_url:
                    res = requests.get(download_url, headers=cls.get_headers(), timeout=30)
                    if res.status_code == 200:
                        _, ext = os.path.splitext(item_path.lower())
                        if ext == ".docx":
                            content = cls.extract_docx_text(res.content)
                        else:
                            content = res.text
                else:
                    content = cls.fetch_raw_file(owner, repo, branch, item_path)
                
                if content is not None:
                    current_files.append({"path": item_path, "content": content})
                    
        return current_files

    @classmethod
    def fetch_raw_file(
        cls, owner: str, repo: str, branch: str, path: str
    ) -> str | None:
        _, ext = os.path.splitext(path.lower())
        if ext == ".docx":
            raw_url = f"{cls.RAW_BASE}/{owner}/{repo}/{branch}/{path}"
            response = requests.get(raw_url, headers=cls.get_headers(), timeout=30)
            if response.status_code == 200:
                return cls.extract_docx_text(response.content)
            return None
        
        raw_url = f"{cls.RAW_BASE}/{owner}/{repo}/{branch}/{path}"
        response = requests.get(raw_url, headers=cls.get_headers(), timeout=30)
        if response.status_code == 200:
            return response.text
        return None

    @classmethod
    def has_allowed_extension(cls, file_path: str) -> bool:
        _, ext = os.path.splitext(file_path.lower())
        return ext in Settings.ALLOWED_EXTENSIONS

    @classmethod
    def is_excluded_path(cls, file_path: str) -> bool:
        normalized = file_path.replace("\\", "/")
        for excluded_dir in Settings.EXCLUDED_DIRS:
            clean_dir = excluded_dir.rstrip("/")
            parts = normalized.split("/")
            if clean_dir in parts:
                return True
        if os.path.basename(normalized) in Settings.EXCLUDED_FILES:
            return True
        return False
