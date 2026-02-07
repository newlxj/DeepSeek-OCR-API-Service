"""
DeepSeek OCR API 服务启动脚本

使用方式:
    python start_api.py

或者使用 uvicorn:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1
"""
import uvicorn
from api.config import API_CONFIG

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=API_CONFIG.host,
        port=API_CONFIG.port,
        reload=API_CONFIG.reload,
        log_level=API_CONFIG.log_level.lower()
    )
