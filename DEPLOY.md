# Hướng dẫn Deploy dự án AI GitHub Grader 🚀

Dự án này gồm hai phần chính:
1. **API Backend (FastAPI)**: Cần được deploy lên một cloud server để có thể truy cập qua Internet.
2. **Chrome/Edge Extension**: Cài đặt trên máy cá nhân và cấu hình kết nối tới địa chỉ của API Backend đã deploy.

---

## 🛠️ PHẦN 1: Deploy API Backend (FastAPI)

Dưới đây là 3 cách deploy Backend từ dễ đến chuyên nghiệp.

### Cách 1: Deploy lên Render.com (Miễn phí & Dễ nhất)

[Render](https://render.com) là dịch vụ cloud cực kỳ phù hợp để chạy thử các dự án nhỏ miễn phí.

1. **Chuẩn bị mã nguồn**:
   - Đưa dự án của bạn lên một repository GitHub cá nhân (ví dụ: `https://github.com/your-username/ai-github-grader`).
2. **Đăng ký/Đăng nhập Render**:
   - Truy cập [dashboard.render.com](https://dashboard.render.com) và kết nối với tài khoản GitHub của bạn.
3. **Tạo Web Service mới**:
   - Nhấn **New +** -> Chọn **Web Service**.
   - Chọn repository GitHub của dự án bạn vừa đẩy lên.
4. **Cấu hình thông tin Web Service**:
   - **Name**: `ai-github-grader-api` (hoặc tên tùy chọn).
   - **Region**: Chọn khu vực gần bạn nhất (ví dụ: Singapore).
   - **Language**: `Python 3` (hoặc chọn **Docker** vì dự án đã có sẵn [Dockerfile](file:///S:/WorkSpace/RikkeiEducation/AutoScoring/Dockerfile)).
   - **Branch**: `main` (hoặc nhánh chứa code mới nhất).
   - *Nếu chọn Language là Python 3 (không dùng Docker)*:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python api.py`
5. **Cấu hình biến môi trường (Environment Variables)**:
   - Nhấn vào nút **Advanced** -> Thêm các biến môi trường cấu hình API Keys:
     - `GEMINI_API_KEY`: Key Gemini của bạn.
     - `DEEPSEEK_API_KEY`: Key DeepSeek (nếu dùng).
     - `GITHUB_TOKEN`: Token GitHub (để tránh bị rate limit khi đọc repo).
6. **Deploy**:
   - Nhấn **Create Web Service**. Render sẽ tự động build và cấp cho bạn một đường dẫn công khai (ví dụ: `https://ai-github-grader-api.onrender.com`).

---

### Cách 2: Deploy lên Railway.app (Nhanh & Tự động nhận Docker)

[Railway](https://railway.app) tự động phát hiện [Dockerfile](file:///S:/WorkSpace/RikkeiEducation/AutoScoring/Dockerfile) và triển khai rất nhanh.

1. Đăng nhập vào Railway bằng GitHub.
2. Chọn **New Project** -> Chọn **Deploy from GitHub repo**.
3. Chọn repo của bạn.
4. Nhấn **Variables** và điền các API Key như `GEMINI_API_KEY` tương tự như cách làm trên Render.
5. Railway sẽ tự động build từ [Dockerfile](file:///S:/WorkSpace/RikkeiEducation/AutoScoring/Dockerfile) và cung cấp URL công khai cho bạn.

---

### Cách 3: Deploy lên VPS riêng bằng Docker (Dành cho Server riêng/Ubuntu)

Nếu bạn có server VPS riêng (như DigitalOcean, AWS, Vultr):

1. **Cài đặt Docker trên VPS**:
   - Chạy lệnh cài đặt Docker và Docker Compose trên Linux.
2. **Clone source code lên VPS**:
   ```bash
   git clone <URL_REPO_CỦA_BẠN>
   cd AutoScoring
   ```
3. **Build Docker Image**:
   ```bash
   docker build -t ai-github-grader .
   ```
4. **Chạy Container**:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e GEMINI_API_KEY="your_gemini_key" \
     -e GITHUB_TOKEN="your_github_token" \
     --name grader-backend \
     ai-github-grader
   ```
5. *Lưu ý*: Để an toàn và có HTTPS (bắt buộc đối với một số trình duyệt), bạn nên cấu hình Nginx làm Reverse Proxy và cài đặt SSL Let's Encrypt cho domain của bạn trỏ về cổng `8000`.

---

## 🔌 PHẦN 2: Cấu hình Chrome/Edge Extension chạy Production

Sau khi deploy thành công Backend và có URL công khai (ví dụ: `https://ai-github-grader-api.onrender.com`):

1. Mở Extension **AI GitHub Grader** trên thanh công cụ của trình duyệt Edge/Chrome.
2. Chuyển sang Tab **Cấu hình (Settings)**.
3. Tại ô **API Backend Server**, thay thế `http://localhost:8000` bằng URL Backend của bạn (ví dụ: `https://ai-github-grader-api.onrender.com`).
4. Nhấn **Lưu cấu hình**.
5. Extension sẽ tự động ping thử tới Server mới và tải danh sách đề bài/tiêu chí từ Server về. Từ giờ bạn có thể tắt máy tính chạy Backend cục bộ đi mà Extension vẫn hoạt động bình thường ở bất kỳ đâu!
