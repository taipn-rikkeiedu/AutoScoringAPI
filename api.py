import os
import sys

# Ngăn Python tạo thư mục __pycache__ (để không bị lỗi khi load Extension trên Chrome/Edge)
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Tự động tắt reload khi chạy trên Render hoặc môi trường production/Docker không có TTY
    is_dev = os.environ.get("ENV", "development").lower() == "development"
    if os.environ.get("RENDER") or not os.isatty(sys.stdout.fileno()):
        is_dev = False
        
    uvicorn.run("extension.api_server:app", host="0.0.0.0", port=port, reload=is_dev)
