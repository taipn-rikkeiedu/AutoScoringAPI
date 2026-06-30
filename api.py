import os
import sys

# Ngăn Python tạo thư mục __pycache__ (để không bị lỗi khi load Extension trên Chrome/Edge)
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("extension.api_server:app", host="0.0.0.0", port=port, reload=True)
