"""
健康检查和状态查询路由
"""
from fastapi import APIRouter, HTTPException
from ..models.responses import HealthResponse, QueueStatusResponse, TaskResponse
from ..services.task_queue import task_queue
from ..services.model_manager import model_manager
from ..config import API_CONFIG

router = APIRouter(tags=["Health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口

    返回服务运行状态和模型加载状态
    """
    return HealthResponse(
        status="running",
        service=API_CONFIG.app_name,
        version=API_CONFIG.version,
        model_loaded=model_manager.is_loaded()
    )


@router.get("/queue/status", response_model=QueueStatusResponse)
async def queue_status():
    """
    队列状态查询

    返回当前队列大小和总任务数
    """
    return QueueStatusResponse(
        queue_size=task_queue.queue_size,
        total_tasks=task_queue.total_tasks
    )


@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态

    返回指定任务的详细信息，包括状态、创建时间、完成时间和结果
    """
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task.to_dict())
