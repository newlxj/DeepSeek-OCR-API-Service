"""
响应数据模型
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class OCRResponse(BaseModel):
    """OCR处理结果响应"""
    code: int
    filename: str
    taskid: str
    bizId: str
    pages: List[str]


class AsyncResponse(BaseModel):
    """异步任务提交响应"""
    code: int
    filename: str
    taskid: str
    bizId: str


class TaskResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    biz_id: str
    filename: str
    status: str
    created_at: float
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None


class QueueStatusResponse(BaseModel):
    """队列状态响应"""
    queue_size: int
    total_tasks: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str = "1.0.0"
    model_loaded: bool = False


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
