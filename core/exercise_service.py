import json
import os
import requests
from core.settings import Settings


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
        if Settings.EXERCISE_SOURCE == "local":
            path = "S:/WorkSpace/AutoScoringConfig/templates.json"
            if not os.path.exists(path):
                path = Settings.LOCAL_TEMPLATES_PATH

            if os.path.exists(path):
                try:
                    with open(
                        path, "r", encoding="utf-8"
                    ) as f:
                        data = json.load(f)
                        if data:
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
                return default_data
            except Exception:
                return default_data

        if Settings.EXERCISE_SOURCE == "remote" and Settings.EXERCISE_API_URL:
            headers = {}
            if Settings.EXERCISE_API_TOKEN:
                headers["Authorization"] = f"Bearer {Settings.EXERCISE_API_TOKEN}"
            response = requests.get(
                Settings.EXERCISE_API_URL, headers=headers, timeout=20
            )
            if response.status_code == 200:
                try:
                    return response.json()
                except Exception:
                    return {}
        return {}

    @classmethod
    def save_templates(cls, templates: dict) -> None:
        path = Settings.LOCAL_TEMPLATES_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
