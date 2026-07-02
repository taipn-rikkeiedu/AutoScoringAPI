# AI GitHub Grader v1.0 🤖

Hệ thống chấm điểm mã nguồn tự động thông qua việc đọc các repository GitHub công khai và đánh giá logic bằng Trí tuệ Nhân tạo (hỗ trợ cả **Gemini Cloud** và **Local AI - Ollama / DeepSeek R1**).

## ✨ Tính năng nổi bật

- **📥 Trích xuất mã nguồn GitHub thông minh**:
  - Hỗ trợ phân tích cây thư mục qua GitHub REST API.
  - **Tự động Fallback ZIP**: Tải gói lưu trữ ZIP trực tiếp từ `codeload.github.com` giúp vượt qua giới hạn lượt gọi API (API Rate Limit) và tự động duyệt thử nhiều nhánh (`main`, `master`,...) để lấy code.
  - **Tự động dọn dẹp đường dẫn**: Loại bỏ thư mục gốc của GitHub (ví dụ: `repo-main/`) giúp AI nhìn thấy sơ đồ thư mục dự án chuẩn xác nhất.
- **⚙️ Quản lý cấu hình AI linh hoạt**:
  - **Google Gemini**: Hỗ trợ đầy đủ các model đời mới (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`,...).
  - **Local AI (Ollama)**: Tận dụng các mô hình chạy offline (như `deepseek-r1:7b`) hoàn toàn miễn phí.
  - **Custom API**: Tương thích hoàn toàn với các nhà cung cấp chuẩn OpenAI API (Groq, OpenRouter, LM Studio,...).
- **📊 Theo dõi tiến trình thời gian thực (Real-time Progress)**:
  - Hiển thị chi tiết từng bước tải và giải nén tệp tin qua bảng trạng thái `st.status()` trực quan.
- **✍️ AI Streaming Output**:
  - Hỗ trợ truyền dữ liệu dạng dòng (Streaming) cho mô hình Local và Custom API, giúp hiển thị phản hồi chấm điểm theo dạng gõ chữ thời gian thực siêu mượt mà.
- **🎯 Chấm điểm có thể cấu hình**:
  - Không hard-code thang điểm, độ dài từ hay ngôn ngữ phản hồi. Mọi thứ dễ dàng cấu hình qua tệp môi trường `.env`.

---

## 📁 Cấu trúc dự án

```text
ai-github-grader/
├── .env                  # Cấu hình biến môi trường & khóa bảo mật (đã ignore)
├── .gitignore            # Khai báo loại trừ các tệp nhạy cảm khi push git
├── requirements.txt      # Khai báo các thư viện Python phụ thuộc
├── app.py                # Giao diện chính (Presentation Layer - Streamlit)
├── config/
│   └── settings.py       # Điểm quản lý cấu hình tập trung của hệ thống
├── services/
│   ├── github_service.py # Xử lý tải, giải nén và phân tích cấu trúc mã nguồn từ GitHub
│   └── ai_service.py     # Điều phối Prompts, quản lý kết nối và stream phản hồi từ AI
└── tests/                # Bộ kiểm thử tự động (Unit Tests)
    ├── test_github_service.py
    └── test_ai_service.py
```

---

## 🛠️ Hướng dẫn cài đặt & Chạy cục bộ (Local)

### Bước 1: Clone dự án và kích hoạt môi trường ảo
```bash
git clone <url-repo-cua-ban>
cd AutoScoring

# Kích hoạt môi trường ảo Python (.venv)
# Trên Windows (PowerShell):
.\.venv\Scripts\activate
# Trên Windows (CMD):
.venv\Scripts\activate.bat
# Trên Git Bash / Linux / macOS:
source .venv/Scripts/activate
```

### Bước 2: Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

### Bước 3: Tạo và cấu hình tệp `.env`
Tạo tệp `.env` tại thư mục gốc và cấu hình như sau:
```env
GEMINI_API_KEY=your_gemini_api_key_if_used
GITHUB_TOKEN=your_github_token_to_increase_rate_limit_if_used

AI_PROVIDER=local
LOCAL_MODEL_NAME=deepseek-r1:7b
OLLAMA_BASE_URL=http://localhost:11434

# Cấu hình thang điểm & định dạng chấm
GRADING_MAX_SCORE=100
GRADING_MAX_WORDS=100
GRADING_LANGUAGE=Tiếng Việt
```

### Bước 4: Khởi chạy ứng dụng
```bash
streamlit run app.py
```

---

## 🧪 Chạy Kiểm thử tự động (Unit Tests)

Dự án đi kèm bộ kiểm thử tự động đầy đủ cho các dịch vụ chính. Để chạy kiểm thử:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## ☁️ Hướng dẫn Deploy lên Streamlit Community Cloud

1. Đẩy mã nguồn dự án lên một repository công khai trên GitHub của bạn.
2. Truy cập [share.streamlit.io](https://share.streamlit.io/) và đăng nhập bằng tài khoản GitHub.
3. Nhấp vào **New app**, chọn Repository, Branch (`main` hoặc `master`), và File chạy chính (`app.py`).
4. Nhấp vào **Advanced settings...** trước khi deploy:
   - Trong ô **Secrets**, dán toàn bộ nội dung tệp cấu hình bí mật của bạn (như `GEMINI_API_KEY`,...) dưới dạng TOML. Ví dụ:
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     GITHUB_TOKEN = "ghp_..."
     ```
5. Bấm **Deploy!** và trải nghiệm hệ thống trên Cloud.
