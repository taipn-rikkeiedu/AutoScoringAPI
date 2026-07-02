import json
import os
import requests
from core.settings import Settings

# Biến toàn cục dùng để lưu trữ cache đề bài trong bộ nhớ đệm (phục vụ test)
_GLOBAL_TEMPLATES = None


class ExerciseService:
    DEFAULT_TEMPLATES = {
        "Bài tập Java OOP (Quản lý sinh viên)": (
            "1. Yêu cầu nghiệp vụ: Thiết kế đúng lớp đối tượng Student (id, name, age, gpa) với encapsulation.\n"
            "2. Logic xử lý: Xây dựng các tính năng CRUD sinh viên chính xác, quản lý danh sách.\n"
            "3. Xử lý ngoại lệ: Bắt lỗi nhập sai định dạng, gpa ngoài khoảng 0-4.\n"
            "4. Chất lượng mã nguồn: Đặt tên chuẩn CamelCase, định dạng code sạch sẽ, dễ đọc."
        ),
        "Bài tập Python FastAPI (API CRUD)": (
            "1. Yêu cầu nghiệp vụ: Đầy đủ các API endpoints CRUD (GET, POST, PUT, DELETE) cho thực thể.\n"
            "2. Logic xử lý: Sử dụng Pydantic để validate dữ liệu đầu vào. Trả về đúng mã HTTP Status Code (201 Created, 404 Not Found).\n"
            "3. Tổ chức mã nguồn: Tách biệt cấu trúc thư mục (routers, schemas, main.py).\n"
            "4. Chất lượng mã nguồn: Sử dụng Type Hinting đầy đủ, viết docstring rõ ràng."
        ),
        "Bài tập Web Frontend (Landing Page)": (
            "1. Yêu cầu nghiệp vụ: Thiết kế Landing Page hiển thị đầy đủ thông tin, bố cục hiện đại.\n"
            "2. Giao diện (CSS): Sử dụng Flexbox/Grid, hỗ trợ giao diện Responsive trên Mobile và Desktop.\n"
            "3. Logic (JavaScript): Tương tác mượt mà (validation form, popup, slider), không lỗi console.\n"
            "4. Cấu trúc: Tổ chức tệp HTML, CSS, JS khoa học, viết CSS có cấu trúc rõ ràng."
        )
    }

    @classmethod
    def load_templates(cls) -> dict:
        global _GLOBAL_TEMPLATES
        if _GLOBAL_TEMPLATES is not None:
            return _GLOBAL_TEMPLATES

        from core.storage_service import get_ai_config
        config = get_ai_config()
        source = config.get("exercise_source", "local").strip().lower()

        if source == "google_sheet":
            url = config.get("google_sheet_url") or Settings.GOOGLE_SHEET_URL
            if url:
                try:
                    return cls.sync_from_google_sheet(url)
                except Exception:
                    pass
            source = "local"

        if source == "local":
            path = Settings.LOCAL_TEMPLATES_PATH

            if os.path.exists(path):
                try:
                    with open(
                        path, "r", encoding="utf-8"
                    ) as f:
                        data = json.load(f)
                        if data:
                            _GLOBAL_TEMPLATES = data
                            return data
                except Exception:
                    pass
            
            # Khởi tạo mặc định theo định dạng phân cấp nếu tệp chưa tồn tại
            default_data = {
                "[Mẫu] Lớp học Python FastAPI": {
                    "Session 1: Giới thiệu FastAPI": {
                        "Bài tập 1: API Hello World": {
                            "assignment": "Hãy viết một API endpoint GET /hello trả về chuỗi chào mừng 'Hello World'.",
                            "criteria": "1. Sử dụng đúng HTTP Method GET.\n2. Endpoint đúng đường dẫn /hello.\n3. Trả về đúng JSON format."
                        }
                    }
                }
            }
            try:
                os.makedirs(os.path.dirname(Settings.LOCAL_TEMPLATES_PATH), exist_ok=True)
                with open(Settings.LOCAL_TEMPLATES_PATH, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
                _GLOBAL_TEMPLATES = default_data
                return default_data
            except Exception:
                _GLOBAL_TEMPLATES = default_data
                return default_data

        if source in ("remote", "api"):
            api_url = config.get("exercise_api_url") or Settings.EXERCISE_API_URL
            api_token = config.get("exercise_api_token") or Settings.EXERCISE_API_TOKEN
            if api_url:
                try:
                    data = cls.fetch_from_api(api_url, api_token)
                    _GLOBAL_TEMPLATES = data
                    return data
                except Exception:
                    pass
        return {}

    @classmethod
    def fetch_from_api(cls, url: str, token: str = None) -> dict:
        """Gọi API REST lấy danh sách đề bài và validate cấu trúc trả về."""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                raise ValueError(f"API HTTP status: {response.status_code}")
            data = response.json()
        except Exception as e:
            raise ValueError(f"Không thể gọi API bài tập: {str(e)}")

        if not isinstance(data, dict):
            raise ValueError("Phản hồi API phải là một đối tượng JSON (dictionary)")

        for ch_name, sessions in data.items():
            if not isinstance(sessions, dict):
                raise ValueError("Cấu trúc phản hồi API bài tập không hợp lệ, phải chứa một đối tượng sessions")
            for sess_name, assignments in sessions.items():
                if not isinstance(assignments, dict):
                    raise ValueError("Cấu trúc phản hồi API bài tập không hợp lệ, phải chứa một đối tượng assignments")
                for ass_name, ass_data in assignments.items():
                    if not isinstance(ass_data, dict):
                        raise ValueError("Bài tập phải là một đối tượng JSON")
                    if "assignment" not in ass_data or "criteria" not in ass_data:
                        raise ValueError("Bài tập phải có chứa trường 'assignment' và 'criteria'")
        return data

    @classmethod
    def sync_from_api_to_local(cls, url: str, token: str = None) -> None:
        """Đồng bộ danh sách đề bài từ API về file cấu hình cục bộ."""
        data = cls.fetch_from_api(url, token)
        cls.save_templates(data)

    @classmethod
    def sync_from_google_sheet(cls, sheet_url: str) -> dict:
        """Đồng bộ dữ liệu bài tập từ một tệp Google Sheet công khai."""
        import csv
        import io
        import re

        # Phân tích URL để trích xuất spreadsheet ID và gid (nếu có)
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        if not match:
            raise ValueError("URL Google Sheet không hợp lệ. Vui lòng dán liên kết chia sẻ chính xác.")
        
        spreadsheet_id = match.group(1)
        gid = None
        gid_match = re.search(r"[#&?]gid=([0-9]+)", sheet_url)
        if gid_match:
            gid = gid_match.group(1)
            
        export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
        if gid:
            export_url += f"&gid={gid}"
            
        # Tải tệp CSV
        response = requests.get(export_url, timeout=15)
        if response.status_code != 200:
            raise ValueError(
                f"Không thể tải dữ liệu từ Google Sheet. Mã lỗi HTTP: {response.status_code}. "
                "Hãy chắc chắn rằng bạn đã chia sẻ Sheet ở chế độ 'Người có liên kết có thể xem'."
            )
            
        csv_text = response.content.decode("utf-8")
        f = io.StringIO(csv_text)
        reader = csv.DictReader(f)
        
        templates = {}
        
        for row in reader:
            chapter = "Chương mặc định"
            session = "Session mặc định"
            title = ""
            assignment = ""
            criteria = ""
            
            # Ánh xạ mềm dẻo các cột (fuzzy matching)
            for key, val in row.items():
                if not key or not val:
                    continue
                key_norm = key.strip().lower()
                val_clean = val.strip()
                
                if any(x in key_norm for x in ("chương", "chapter", "chuong")):
                    chapter = val_clean
                elif any(x in key_norm for x in ("session", "buổi", "buoi")):
                    session = val_clean
                elif any(x in key_norm for x in ("tên bài", "ten bai", "bài tập", "bai tap", "assignment name", "title")):
                    title = val_clean
                elif any(x in key_norm for x in ("đề bài", "de bai", "content", "assignment")):
                    assignment = val_clean
                elif any(x in key_norm for x in ("tiêu chí", "tieu chi", "criteria")):
                    criteria = val_clean
            
            # Fallback nếu header không khớp: thử lấy theo thứ tự chỉ số
            if not title:
                keys = list(row.keys())
                if len(keys) >= 3:
                    chapter = row.get(keys[0], chapter).strip()
                    session = row.get(keys[1], session).strip()
                    title = row.get(keys[2], "").strip()
                    assignment = row.get(keys[3], "") if len(keys) > 3 else ""
                    criteria = row.get(keys[4], "") if len(keys) > 4 else ""
                    
            if not title or not assignment:
                continue
                
            if chapter not in templates:
                templates[chapter] = {}
            if session not in templates[chapter]:
                templates[chapter][session] = {}
                
            templates[chapter][session][title] = {
                "assignment": assignment,
                "criteria": criteria or Settings.DEFAULT_CRITERIA
            }
            
        if templates:
            # Lưu bản sao lưu cục bộ
            cls.save_templates(templates)
            
        return templates

    @classmethod
    def get_source(cls) -> str:
        """Lấy nguồn bài tập đang cấu hình."""
        from core.storage_service import get_ai_config
        config = get_ai_config()
        return config.get("exercise_source", "local").strip().lower()

    @classmethod
    def save_templates(cls, templates: dict) -> None:
        global _GLOBAL_TEMPLATES
        _GLOBAL_TEMPLATES = templates
        path = Settings.LOCAL_TEMPLATES_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
