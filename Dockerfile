# Sử dụng Python image chính thức
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Thiết lập các biến môi trường tối ưu cho Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Sao chép file requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn của dự án vào container
COPY . .

# Mở cổng kết nối
EXPOSE 8000

# Lệnh khởi chạy ứng dụng (chạy thông qua api.py và tự động nhận PORT từ môi trường)
CMD ["python", "api.py"]
