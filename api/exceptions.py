"""
自定义异常类
"""


class APIException(Exception):
    """API异常基类"""

    def __init__(self, message: str, code: int = 500, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class ModelNotLoadedException(APIException):
    """模型未加载异常"""

    def __init__(self, message: str = "Model not loaded yet"):
        super().__init__(message, code=503, status_code=503)


class TaskNotFoundException(APIException):
    """任务未找到异常"""

    def __init__(self, task_id: str):
        super().__init__(f"Task {task_id} not found", code=404, status_code=404)


class FileProcessingException(APIException):
    """文件处理异常"""

    def __init__(self, message: str):
        super().__init__(message, code=422, status_code=422)


class InvalidParameterException(APIException):
    """参数异常"""

    def __init__(self, message: str):
        super().__init__(message, code=400, status_code=400)


class QueueFullException(APIException):
    """队列已满异常"""

    def __init__(self, message: str = "Task queue is full"):
        super().__init__(message, code=503, status_code=503)
