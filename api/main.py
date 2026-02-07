"""
FastAPI应用入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import API_CONFIG
from .routes.ocr import router as ocr_router
from .routes.health import router as health_router
from .services.task_queue import task_queue
from .services.ocr_service import OCRService
from .services.callback_service import CallbackService
from .exceptions import APIException
from .utils.file_utils import cleanup_temp_file

# 配置日志
logging.basicConfig(
    level=API_CONFIG.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"Starting {API_CONFIG.app_name} v{API_CONFIG.version}...")

    # 定义异步任务处理函数
    async def process_task(task):
        """处理队列中的任务"""
        ocr_svc = OCRService()
        callback_svc = CallbackService()

        try:
            if task.task_type == "pdf":
                # 处理PDF
                result_pages = await ocr_svc.process_pdf(
                    task.data['temp_path'],
                    skip_pages=task.data.get('skip_pages'),
                    limit_pages=task.data.get('limit_pages'),
                    det=task.data.get('det', False)
                )
                # 清理临时文件
                cleanup_temp_file(task.data['temp_path'])

            elif task.task_type == "image":
                # 处理单张图片
                result_pages = [await ocr_svc.process_image(
                    task.data['image'],
                    det=task.data.get('det', False)
                )]

            elif task.task_type == "images":
                # 处理多张图片
                result_pages = await ocr_svc.process_images_batch(
                    task.data['images'],
                    det=task.data.get('det', False)
                )

            # 构建成功结果
            result = {
                "code": 200,
                "filename": task.filename,
                "taskid": task.task_id,
                "bizId": task.biz_id,
                "pages": result_pages
            }

            # 发送回调
            if task.callback_url:
                await callback_svc.send_callback(task.callback_url, result)

            return result

        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {str(e)}", exc_info=True)

            # 构建错误结果
            error_result = {
                "code": 500,
                "filename": task.filename,
                "taskid": task.task_id,
                "bizId": task.biz_id,
                "error": str(e)
            }

            # 清理临时文件
            if task.task_type == "pdf" and task.data.get('temp_path'):
                cleanup_temp_file(task.data['temp_path'])

            # 发送错误回调
            if task.callback_url:
                await callback_svc.send_callback(task.callback_url, error_result)

            raise

        finally:
            await callback_svc.close()

    # 启动任务队列处理器
    await task_queue.start_processor(process_task)

    yield

    # 关闭时
    logger.info("Shutting down...")
    await task_queue.stop_processor()


# 创建FastAPI应用
app = FastAPI(
    title=API_CONFIG.app_name,
    description="OCR service for converting PDFs and images to Markdown",
    version=API_CONFIG.version,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG.cors_origins,
    allow_credentials=API_CONFIG.cors_allow_credentials,
    allow_methods=API_CONFIG.cors_allow_methods,
    allow_headers=API_CONFIG.cors_allow_headers,
)


# 异常处理器
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """处理自定义API异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "Internal server error"}
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


# 注册路由
app.include_router(ocr_router)
app.include_router(health_router)
