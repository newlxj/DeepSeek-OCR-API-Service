"""
API服务配置
"""
from pydantic_settings import BaseSettings
from typing import List


class APIConfig(BaseSettings):
    """API服务配置"""

    # 服务配置
    app_name: str = "DeepSeek OCR Service"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "INFO"
    max_upload_size: int = 100 * 1024 * 1024  # 100MB

    # CORS配置
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # 任务队列配置
    max_queue_size: int = 1000

    # 回调配置
    callback_timeout: int = 30  # 秒

    class Config:
        env_file = ".env"
        env_prefix = "API_"
        case_sensitive = False


# 全局配置实例
API_CONFIG = APIConfig()
