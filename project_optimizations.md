# Báo cáo các giải pháp Tối ưu hóa & Điểm nổi bật trong Dự án AI GitHub Grader 🛠️

Tài liệu này tổng hợp toàn bộ các giải pháp tối ưu hóa kỹ thuật nâng cao được triển khai trong hệ thống **AI GitHub Grader**, tập trung vào kiến trúc **Headless API Backend (FastAPI)**, **Chrome/Edge Extension**, và các dịch vụ xử lý lõi (Core Services). Phần tài liệu này đã được lược bỏ toàn bộ các tham chiếu liên quan đến Streamlit.

---

## 🌲 1. Tối ưu hóa Thu thập & Xử lý Mã nguồn từ GitHub

Bộ phận dịch vụ GitHub ([github_service.py](file:///s:/WorkSpace/AutoScoring/core/github_service.py)) được thiết kế để giải quyết bài toán tải mã nguồn hiệu năng cao, tránh tối đa giới hạn băng thông/lượt gọi API (Rate Limit) của GitHub và định dạng hóa dữ liệu chuẩn chỉnh trước khi đưa vào AI.

### A. Chiến lược tải ZIP lưu trữ (Fastest Path - Tiết kiệm Rate Limit)
*   **Vấn đề:** Khi truy xuất mã nguồn qua GitHub REST API truyền thống, hệ thống phải thực hiện đệ quy duyệt cây thư mục và gửi hàng chục hoặc hàng trăm yêu cầu HTTP GET để lấy nội dung từng tệp tin. Điều này cực kỳ chậm và dễ dàng làm cạn kiệt API Rate Limit của GitHub (chỉ giới hạn 60 lượt gọi/giờ đối với IP không xác thực).
*   **Giải pháp:** Hệ thống ưu tiên tải xuống toàn bộ mã nguồn của repository dưới dạng một gói ZIP nén duy nhất thông qua liên kết `https://codeload.github.com/{username}/{repo}/zip/refs/heads/{branch}`. 
    *   Chỉ sử dụng đúng **1 yêu cầu HTTP duy nhất** để lấy toàn bộ dữ liệu.
    *   Việc giải nén và xử lý tệp tin được thực hiện hoàn toàn trong bộ nhớ đệm RAM bằng cách sử dụng `io.BytesIO` và thư viện `zipfile` của Python, không sinh ra tệp tin tạm trên ổ cứng, giúp tối ưu hóa tốc độ I/O.

### B. Cơ chế tự động Fallback đa cấp (Multi-stage Fallback Sequence)
Nếu quá trình tải tệp ZIP lưu trữ bị thất bại hoặc bị chặn, hệ thống sẽ tự động thực hiện quy trình hạ cấp dịch vụ theo thứ tự ưu tiên giảm dần để đảm bảo tính sẵn sàng:
1.  **ZIP Archive:** Thử tải tệp ZIP lần lượt qua các nhánh ứng viên (nhánh mặc định lấy từ API, hoặc fallback sang `main`, `master`).
2.  **Git Trees API:** Chuyển sang gọi API cây thư mục đệ quy của GitHub `/git/trees/{branch}?recursive=1` để lấy sơ đồ cấu trúc thư mục dạng JSON chỉ với 1 request bổ sung.
3.  **Contents API:** Nếu Trees API không khả dụng, hệ thống tiếp tục hạ cấp xuống duyệt thư mục gốc thông qua `/contents`.
4.  **Tải tệp tin riêng lẻ:** Chỉ khi xác định được danh sách tệp tin thông qua các API trên, hệ thống mới tiến hành tải nội dung từng tệp. Nếu tệp tin có trường `download_url`, hệ thống sẽ tải trực tiếp; nếu là đối tượng dạng `blob`, hệ thống sẽ tải qua raw URL của GitHub (`raw.githubusercontent.com/...`) để đảm bảo không bị lỗi mã hóa.

### C. Định dạng & Làm sạch đường dẫn (Path Cleansing)
*   Khi tải tệp ZIP từ GitHub, cấu trúc thư mục giải nén mặc định luôn bị chèn một thư mục gốc có dạng `tên-repo-tên-nhánh/` (ví dụ: `AutoScoring-main/`).
*   Nếu chuyển trực tiếp đường dẫn này cho AI, AI sẽ bị nhầm lẫn cấu trúc thư mục thực tế của dự án.
*   **Giải pháp:** Hệ thống tự động xác định tiền tố dùng chung ở cấp cao nhất này và cắt bỏ nó ra khỏi đường dẫn hiển thị (`name[len(prefix):]`). Kết quả là AI sẽ nhìn thấy một cấu trúc thư mục sạch sẽ, chuẩn hóa (ví dụ: `core/ai_service.py` thay vì `AutoScoring-main/core/ai_service.py`).

### D. Bộ lọc nội dung thông minh & Giới hạn an toàn (Guardrails)
*   **Loại bỏ tệp tin rác:** Loại trừ toàn bộ các thư mục phụ trợ, mã dịch, hoặc thư viện bên thứ ba thông qua bộ lọc thư mục `EXCLUDED_DIRS` (như `node_modules/`, `.venv`, `.git/`, `build/`, `dist/`, `__pycache__/`) và bộ lọc tệp tin `EXCLUDED_FILES` (như `package-lock.json`, `yarn.lock`, `.gitignore`, `LICENSE`).
*   **Chỉ duyệt mã nguồn hợp lệ:** Chỉ đọc các tệp tin có đuôi định dạng nằm trong danh sách trắng `ALLOWED_EXTENSIONS`.
*   **Tránh tràn ngữ cảnh (Context Overflow):** Hệ thống giám sát chặt chẽ số lượng tệp tin (`MAX_PROJECT_FILES`) và tổng dung lượng ký tự (`MAX_PROJECT_CHARS`). Nếu vượt quá ngưỡng cấu hình, hệ thống sẽ dừng ngay lập tức và đưa ra cảnh báo tường minh thay vì gửi yêu cầu lỗi sang AI API gây lãng phí chi phí.

### E. Trích xuất tài liệu Word `.docx` động
*   Nhiều bài tập hoặc yêu cầu nghiệp vụ được lưu dưới dạng tài liệu Word `.docx` (vốn là một tệp lưu trữ ZIP chứa mã nguồn XML).
*   Thay vì bỏ qua hoặc lỗi đọc, `GitHubService` sẽ phát hiện phần mở rộng `.docx`, giải nén tệp tin đó trong bộ nhớ, đọc nội dung tệp `word/document.xml`, sử dụng bộ phân tích cú pháp XML `ElementTree` để lấy toàn bộ các đoạn văn bản nằm trong thẻ `<w:t>` và ghép nối lại thành chuỗi văn bản sạch. AI có thể đọc đề bài hoặc tài liệu mô tả này để chấm điểm logic mã nguồn tương ứng.

---

## 💰 2. Tối ưu hóa Chi phí Token & Hiệu năng AI

Hệ thống triển khai các giải pháp xử lý văn bản đầu vào và cơ chế lưu trữ để hạn chế tối đa tài nguyên tiêu thụ khi làm việc với AI API.

### A. Thuật toán nén mã nguồn giảm thiểu Token (`_compress_code`)
Để tối ưu hóa dung lượng Prompt đầu vào gửi tới AI, hàm `_compress_code` trong [ai_service.py](file:///s:/WorkSpace/AutoScoring/core/ai_service.py) thực hiện:
*   Loại bỏ toàn bộ các khoảng trắng thừa ở cuối mỗi dòng lệnh (`line.rstrip()`).
*   Phát hiện và nén nhiều dòng trống liên tiếp thành tối đa một dòng trống duy nhất để giữ lại cấu trúc phân đoạn trực quan nhưng không làm hao tổn token.
*   Giải pháp này giúp giảm từ **15% đến 30% tổng số lượng token đầu vào**, trực tiếp giảm chi phí hóa đơn API và tăng tốc độ xử lý của mô hình AI.

### B. Bộ nhớ đệm chấm điểm cục bộ (SHA-256 Cache Engine)
*   **Cơ chế khóa băm (Cache Key):** Tạo mã hash SHA-256 duy nhất đại diện cho tổ hợp: `Đề bài + Tiêu chí chấm điểm + Nội dung toàn bộ mã nguồn của dự án`.
*   **Kiểm tra Cache:** Trước khi thực hiện bất kỳ yêu cầu chấm điểm nào bằng AI, hệ thống sẽ đối chiếu mã hash này với bộ nhớ đệm [cache_service.py](file:///s:/WorkSpace/AutoScoring/core/cache_service.py).
*   **Cache HIT:** Nếu phát hiện kết quả trùng khớp và thời gian lưu cache chưa vượt quá giới hạn cấu hình `GRADING_CACHE_TTL_MINUTES`, hệ thống lập tức trả về báo cáo chấm điểm cũ chỉ trong vài mili-giây, bỏ qua hoàn toàn bước gọi AI API.
*   **Cache MISS:** Khi cache bị trượt, hệ thống gọi AI chấm điểm, sau đó tự động lưu kết quả mới vào cache phục vụ cho các lần truy vấn tiếp theo.

---

## ⚡ 3. Cơ chế AI Tin cậy, Tự động Retry & Streaming UTF-8 an toàn

Dịch vụ AI ([ai_service.py](file:///s:/WorkSpace/AutoScoring/core/ai_service.py)) được tinh chỉnh để chạy ổn định trước các biến động mạng và hạn chế kỹ thuật của dòng dữ liệu truyền tải.

### A. Tích hợp đa dạng nhà cung cấp AI (Model Routing)
*   Hỗ trợ tương thích toàn diện từ các mô hình thương mại hiệu năng cao như **Google Gemini** (`gemini-2.5-flash`, `gemini-2.5-pro`...) thông qua kết nối REST trực tiếp (không phụ thuộc SDK nặng nề), đến các dịch vụ trung gian như **OpenRouter**, **DeepSeek API**, và các **Custom API** chuẩn OpenAI.
*   Hỗ trợ chạy mô hình cục bộ **Local AI (Ollama)** hoàn toàn miễn phí và bảo mật dữ liệu tuyệt đối (ví dụ sử dụng `deepseek-r1:7b`).

### B. Cơ chế tự động thử lại kèm dãn cách tăng dần (Exponential Backoff & Rate-Limit Reading)
*   Hệ thống thiết lập cơ chế tự động thử lại tối đa 5 lần đối với các lỗi kết nối tạm thời hoặc quá tải API (HTTP 429 và 503).
*   **Đọc phản hồi thông minh:** Hệ thống không chờ đợi theo các khoảng thời gian cố định một cách thụ động. Thay vào đó, nó sẽ:
    1.  Kiểm tra tiêu đề phản hồi `Retry-After` từ máy chủ để lấy số giây cần chờ.
    2.  Nếu không có tiêu đề, hệ thống dùng biểu thức chính quy (Regex) quét qua nội dung văn bản lỗi để tìm các cụm từ chỉ định thời gian chờ (ví dụ: *"please retry in XXs"*).
    3.  Nếu không tìm thấy thông tin cụ thể, hệ thống sẽ áp dụng thuật toán dãn cách lũy thừa: $Delay = BaseDelay \times 2^{attempt}$.

### C. Cơ chế xử lý dòng dữ liệu thô UTF-8 an toàn (`_iter_lines_safe`)
*   **Vấn đề:** Khi sử dụng tính năng truyền dữ liệu dạng dòng (Streaming) để hiển thị kết quả gõ chữ thời gian thực cho người dùng, dữ liệu trả về từ API dạng Server-Sent Events (SSE) được phân mảnh thành các khối byte thô. Tiếng Việt là ngôn ngữ đa byte (Multi-byte UTF-8). Nếu một ký tự tiếng Việt có dấu bị chia cắt ngẫu nhiên nằm ở ranh giới giữa hai gói tin HTTP khác nhau, việc giải mã thô từng gói tin sẽ tạo ra các ký tự lỗi hiển thị (mojibake hoặc hình ô vuông dấu hỏi).
*   **Giải pháp:** Tự xây dựng hàm `_iter_lines_safe` sử dụng bộ giải mã tăng dần `codecs.getincrementaldecoder("utf-8")`. Bộ giải mã này sẽ giữ lại các byte lẻ chưa đủ cấu thành một ký tự hoàn chỉnh ở cuối gói tin hiện tại, và chỉ giải mã chúng khi nhận được gói tin tiếp theo chứa các byte còn lại. Giải pháp này đảm bảo luồng văn bản tiếng Việt luôn được tái cấu trúc hoàn hảo và mượt mà trên giao diện extension.

---

## 🛠️ 4. Kiến trúc Headless API Server & Trải nghiệm Browser Extension

Dự án được cấu trúc hóa để chạy cực kỳ tối giản và hiệu quả khi hoạt động không có Streamlit.

### A. FastAPI Server hiệu năng cao ([api_server.py](file:///s:/WorkSpace/AutoScoring/extension/api_server.py))
*   Xây dựng hệ thống endpoint RESTful API tinh gọn để kết nối trực tiếp giữa Chrome Extension và lõi Python Core:
    *   `GET /api/config`: Trả về thông tin AI Provider đang được kích hoạt và cấu hình hệ thống (ẩn đi các trường nhạy cảm như API Key để bảo mật).
    *   `GET /api/exercises`: Nạp nhanh danh sách cấu trúc bài tập.
    *   `POST /api/grade`: Nhận yêu cầu chấm điểm, điều phối quy trình tải GitHub -> Chấm điểm AI -> Parse điểm -> Trả kết quả JSON.
*   Tích hợp sẵn cấu hình CORS (`allow_origins=["*"]`) cho phép Tiện ích mở rộng của trình duyệt (Chrome/Edge Extension) truy cập tài nguyên từ các nguồn gốc khác nhau một cách an toàn.

### B. Trải nghiệm Chrome Extension một chạm ([popup.js](file:///s:/WorkSpace/AutoScoring/extension/popup.js))
*   **Auto-fill URL thông minh:** Khi kích hoạt popup extension, mã script nền sử dụng API `chrome.tabs.query` để quét URL của tab hiện tại. Sử dụng biểu thức chính quy:
    ```javascript
    url.match(/^https?:\/\/(www\.)?github\.com\/([^/]+)\/([^/]+)/)
    ```
    để lọc ra chính xác địa chỉ gốc của dự án GitHub (loại bỏ các tham số phụ như query string, hash) và tự động điền vào ô nhập liệu cho giáo viên.
*   **Giao diện chuyển đổi tab mượt mà:** Cho phép cấu hình nhanh địa chỉ API Server ngay trên giao diện extension và kiểm tra trạng thái kết nối thời gian thực thông qua banner thông báo trực quan.
*   **Tích hợp Marked.js:** Nhúng thư viện phân tích cú pháp Markdown gọn nhẹ trực tiếp trong extension để chuyển đổi báo cáo Markdown của AI thành cấu trúc HTML dạng bảng điểm sắc nét ngay trên popup trình duyệt.

### C. Đồng bộ hóa tệp cấu hình không phụ thuộc Session (`storage_service.py` & `sync_service.py`)
*   Vì đã loại bỏ Streamlit Session State, các cấu hình AI và thư viện bài tập được đồng bộ hóa và quản lý tập trung thông qua ổ đĩa máy tính cục bộ tại đường dẫn `C:/AutoScoring/` (`LOCAL_DATA_ROOT`).
*   Mỗi khi backend khởi chạy hoặc có yêu cầu thay đổi cấu hình, `sync_service.py` sẽ thực hiện ghi trực tiếp các cấu trúc JSON xuống đĩa cứng để bảo toàn trạng thái cấu hình AI giữa các lần khởi động Server API.
*   Hỗ trợ cấu hình nguồn bài tập kép: Giáo viên có thể nạp bài tập từ file JSON cục bộ hoặc gọi REST API của trường học để đồng bộ về máy tính cục bộ, sau đó API Server sẽ phân phối lại cho Chrome Extension.
