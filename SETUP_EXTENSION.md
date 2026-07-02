# Hướng dẫn cài đặt và sử dụng AI GitHub Grader (Bản Extension + API Backend) 🚀

Tài liệu này hướng dẫn chi tiết cách clone, thiết lập và chạy hệ thống chấm điểm tự động mã nguồn GitHub sử dụng **Chrome/Edge Extension** kết hợp **API Backend (FastAPI)** mà không cần sử dụng giao diện Streamlit.

---

## 📋 Yêu cầu hệ thống
- **Python**: Phiên bản 3.10 trở lên.
- **Git**: Để clone mã nguồn.
- **Trình duyệt**: Google Chrome, Microsoft Edge hoặc các trình duyệt nhân Chromium.

---

## 🛠️ Các bước thiết lập hệ thống

### Bước 1: Clone mã nguồn dự án
Mở terminal (Git Bash, Command Prompt hoặc PowerShell) và chạy lệnh:
```bash
git clone <URL_REPOSITORY_CỦA_BẠN>
cd AutoScoring
```

### Bước 2: Khởi tạo môi trường ảo (Virtual Environment)
Tạo môi trường ảo cách ly để cài đặt các thư viện Python:
```bash
python -m venv .venv
```

**Kích hoạt môi trường ảo:**
- **Trên Windows (PowerShell)**:
  ```powershell
  .\.venv\Scripts\activate
  ```
- **Trên Windows (Git Bash / Linux / macOS)**:
  ```bash
  source ./.venv/Scripts/activate
  ```
- **Trên Windows (Command Prompt - CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

### Bước 3: Cài đặt các thư viện cần thiết
Vì chỉ sử dụng Extension và API Backend (không chạy giao diện web Streamlit), bạn chỉ cần cài đặt các thư viện cốt lõi bằng lệnh:
```bash
pip install fastapi uvicorn requests python-dotenv google-generativeai
```

### Bước 4: Cấu hình biến môi trường (`.env`)
Tạo tệp tên là `.env` tại thư mục gốc của dự án (`AutoScoring/`) và điền các khóa API cấu hình như sau:

```env
# API Key của Google Gemini để thực hiện chấm điểm bằng AI
GEMINI_API_KEY=AIzaSy...

# GitHub Token (Tùy chọn) - Giúp tăng giới hạn lượt gọi API (Rate Limit) khi tải code từ GitHub
GITHUB_TOKEN=ghp_...

# Nguồn bài tập mặc định (Mặc định là local)
EXERCISE_SOURCE=local
```

---

## 🏃 Chạy API Backend và Cài đặt Extension

### Bước 1: Khởi chạy API Backend
Khi môi trường ảo `.venv` đang hoạt động, khởi động API Server bằng lệnh:
```bash
python api.py
```
*Hệ thống sẽ chạy một FastAPI server cục bộ tại địa chỉ `http://localhost:8000`. Bạn có thể kiểm tra danh sách API tài liệu tương tác tại `http://localhost:8000/docs`.*

### Bước 2: Cài đặt tiện ích Extension lên trình duyệt
1. Mở trình duyệt Chrome hoặc Edge và đi tới trang quản lý tiện ích:
   - **Chrome**: Truy cập `chrome://extensions/`
   - **Edge**: Truy cập `edge://extensions/`
2. Bật công tắc **Developer mode (Chế độ nhà phát triển)** (thường nằm ở góc trên bên phải).
3. Bấm vào nút **Load unpacked (Tải tiện ích đã giải nén)** ở góc trái.
4. Chọn thư mục `extension` trong thư mục dự án của bạn (đường dẫn dạng: `...\AutoScoring\extension`).

---

## 🎯 Hướng dẫn sử dụng
1. **Kết nối Server**:
   - Nhấp vào biểu tượng Extension **AI GitHub Grader** trên thanh công cụ trình duyệt.
   - Chuyển sang tab **⚙️ Cài Đặt (Settings)**.
   - Nhập URL API Backend của bạn (Mặc định là `http://localhost:8000`) và bấm **Lưu Cấu Hình**.
   - Trạng thái kết nối sẽ đổi sang màu xanh lá cây báo **Đã kết nối**.

2. **Tiến hành chấm điểm**:
   - Truy cập vào trang GitHub chứa mã nguồn bài tập của học viên (ví dụ: `https://github.com/hocvien/bai-tap-1`).
   - Click mở Extension. URL GitHub sẽ tự động được điền vào ô **GitHub Repository URL**.
   - Chọn **Chương**, **Session** và **Bài tập** tương ứng từ dropdown (danh sách được tải động từ API Backend).
   - Nhấn nút **🚀 Bắt đầu Chấm điểm**. Kết quả điểm số cùng báo cáo chi tiết dạng bảng và Markdown sẽ hiển thị ngay lập tức trong cửa sổ popup.
