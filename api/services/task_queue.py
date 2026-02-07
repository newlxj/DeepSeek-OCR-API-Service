"""
任务队列管理
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    biz_id: str
    filename: str
    task_type: str  # 'pdf', 'image', 'images'
    is_async: bool
    callback_url: Optional[str] = None
    status: TaskStatus = TaskStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None  # 存储任务处理所需数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "biz_id": self.biz_id,
            "filename": self.filename,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error
        }


class TaskQueue:
    """FIFO任务队列"""

    def __init__(self, max_size: int = 1000):
        self._queue: deque[Task] = deque()
        self._tasks: Dict[str, Task] = {}
        self._processing = False
        self._lock = asyncio.Lock()
        self._total_count = 0
        self._max_size = max_size
        self._process_func: Optional[Callable] = None
        self._processor_task: Optional[asyncio.Task] = None

    async def enqueue(self, task: Task) -> str:
        """
        将任务加入队列

        Args:
            task: 任务对象

        Returns:
            str: 任务ID

        Raises:
            QueueFullException: 队列已满
        """
        async with self._lock:
            if len(self._queue) >= self._max_size:
                from ..exceptions import QueueFullException
                raise QueueFullException()

            self._queue.append(task)
            self._tasks[task.task_id] = task
            self._total_count += 1
            logger.info(f"Task {task.task_id} enqueued, queue size: {len(self._queue)}")
        return task.task_id

    async def dequeue(self) -> Optional[Task]:
        """
        从队列取出任务

        Returns:
            Optional[Task]: 任务对象，队列为空时返回None
        """
        async with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft()

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            Optional[Task]: 任务对象，不存在时返回None
        """
        return self._tasks.get(task_id)

    async def update_task(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            result: 处理结果
            error: 错误信息
        """
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                task.completed_at = time.time()
            logger.info(f"Task {task_id} updated to {status.value}")

    @property
    def queue_size(self) -> int:
        """当前队列大小"""
        return len(self._queue)

    @property
    def total_tasks(self) -> int:
        """总任务数"""
        return self._total_count

    async def start_processor(self, process_func: Callable) -> None:
        """
        启动队列处理器

        Args:
            process_func: 处理函数，接收Task对象作为参数
        """
        if self._processing:
            logger.warning("Processor already running")
            return

        self._processing = True
        self._process_func = process_func
        self._processor_task = asyncio.create_task(self._process_loop())
        logger.info("Task queue processor started")

    async def stop_processor(self) -> None:
        """停止队列处理器"""
        self._processing = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Task queue processor stopped")

    async def _process_loop(self) -> None:
        """队列处理循环"""
        while self._processing:
            task = await self.dequeue()
            if task is None:
                await asyncio.sleep(0.1)
                continue

            await self.update_task(task.task_id, TaskStatus.PROCESSING)

            try:
                result = await self._process_func(task)
                await self.update_task(task.task_id, TaskStatus.COMPLETED, result=result)
            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {str(e)}")
                await self.update_task(task.task_id, TaskStatus.FAILED, error=str(e))

    async def cleanup_old_tasks(self, max_age: float = 3600) -> int:
        """
        清理旧任务

        Args:
            max_age: 任务最大保留时间（秒）

        Returns:
            int: 清理的任务数
        """
        current_time = time.time()
        to_remove = []

        async with self._lock:
            for task_id, task in self._tasks.items():
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    if task.completed_at and (current_time - task.completed_at) > max_age:
                        to_remove.append(task_id)

            for task_id in to_remove:
                del self._tasks[task_id]

        logger.info(f"Cleaned up {len(to_remove)} old tasks")
        return len(to_remove)


# 全局任务队列实例
task_queue = TaskQueue()
