"""
OCR处理路由
"""
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image

from ..models.responses import OCRResponse
from ..services.ocr_service import OCRService
from ..services.task_queue import task_queue, Task, TaskStatus
from ..utils.file_utils import load_image_from_upload, save_upload_file_tmp, cleanup_temp_file
from ..utils.file_utils import validate_pdf_file, validate_image_file

router = APIRouter(prefix="/ocr", tags=["OCR"])

# 全局OCR服务实例
ocr_service = OCRService()


@router.post("/pdf")
async def ocr_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    biz_id: str = Form(..., description="业务ID"),
    is_async: bool = Form(False, description="是否异步处理"),
    callback_url: Optional[str] = Form(None, description="回调地址"),
    skip_pages: Optional[str] = Form(None, description="跳过的页码，逗号分隔"),
    limit_pages: Optional[int] = Form(None, description="限制处理页数"),
    det: bool = Form(False, description="是否输出检测位置信息")
):
    """
    PDF转Markdown

    支持同步和异步两种处理模式。
    同步模式直接返回处理结果，异步模式立即返回任务ID，处理完成后通过callback_url通知。
    """
    # 验证文件类型
    if not validate_pdf_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are supported.")

    # 验证异步模式参数
    if is_async and not callback_url:
        raise HTTPException(status_code=400, detail="callback_url is required for async mode")

    # 解析skip_pages
    skip_pages_list = None
    if skip_pages:
        try:
            skip_pages_list = [int(x.strip()) for x in skip_pages.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid skip_pages format")

    task_id = str(uuid.uuid4())

    if is_async:
        # 异步处理 - 保存临时文件并加入队列
        temp_path = await save_upload_file_tmp(file)

        task = Task(
            task_id=task_id,
            biz_id=biz_id,
            filename=file.filename,
            task_type="pdf",
            is_async=True,
            callback_url=callback_url,
            data={
                "temp_path": temp_path,
                "skip_pages": skip_pages_list,
                "limit_pages": limit_pages,
                "det": det
            }
        )

        await task_queue.enqueue(task)

        return JSONResponse(
            status_code=220,
            content={
                "code": 220,
                "filename": file.filename,
                "taskid": task_id,
                "bizId": biz_id
            }
        )
    else:
        # 同步处理 - 直接处理
        temp_path = await save_upload_file_tmp(file)

        try:
            pages = await ocr_service.process_pdf(
                temp_path,
                skip_pages=skip_pages_list,
                limit_pages=limit_pages,
                det=det
            )

            return OCRResponse(
                code=200,
                filename=file.filename,
                taskid=task_id,
                bizId=biz_id,
                pages=pages
            )
        finally:
            cleanup_temp_file(temp_path)


@router.post("/image")
async def ocr_image(
    file: UploadFile = File(..., description="图片文件"),
    biz_id: str = Form(..., description="业务ID"),
    is_async: bool = Form(False, description="是否异步处理"),
    callback_url: Optional[str] = Form(None, description="回调地址"),
    det: bool = Form(False, description="是否输出检测位置信息")
):
    """
    单张图片转Markdown

    支持的图片格式：jpg, jpeg, png, bmp, tiff, webp
    """
    # 验证文件类型
    if not validate_image_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Only image files are supported.")

    # 验证异步模式参数
    if is_async and not callback_url:
        raise HTTPException(status_code=400, detail="callback_url is required for async mode")

    task_id = str(uuid.uuid4())

    if is_async:
        # 异步处理 - 加载图片并加入队列
        image = await load_image_from_upload(file)

        task = Task(
            task_id=task_id,
            biz_id=biz_id,
            filename=file.filename,
            task_type="image",
            is_async=True,
            callback_url=callback_url,
            data={"image": image, "det": det}
        )

        await task_queue.enqueue(task)

        return JSONResponse(
            status_code=220,
            content={
                "code": 220,
                "filename": file.filename,
                "taskid": task_id,
                "bizId": biz_id
            }
        )
    else:
        # 同步处理
        image = await load_image_from_upload(file)
        result = await ocr_service.process_image(image, det=det)

        return OCRResponse(
            code=200,
            filename=file.filename,
            taskid=task_id,
            bizId=biz_id,
            pages=[result]
        )


@router.post("/images")
async def ocr_images(
    files: List[UploadFile] = File(..., description="多个图片文件"),
    biz_id: str = Form(..., description="业务ID"),
    is_async: bool = Form(False, description="是否异步处理"),
    callback_url: Optional[str] = Form(None, description="回调地址"),
    det: bool = Form(False, description="是否输出检测位置信息")
):
    """
    多张图片批量转Markdown

    支持的图片格式：jpg, jpeg, png, bmp, tiff, webp
    """
    # 验证文件类型
    for file in files:
        if not validate_image_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Only image files are supported."
            )

    # 验证异步模式参数
    if is_async and not callback_url:
        raise HTTPException(status_code=400, detail="callback_url is required for async mode")

    task_id = str(uuid.uuid4())
    filenames = [file.filename for file in files]

    if is_async:
        # 异步处理 - 加载图片并加入队列
        images = []
        for file in files:
            image = await load_image_from_upload(file)
            images.append(image)

        task = Task(
            task_id=task_id,
            biz_id=biz_id,
            filename=",".join(filenames),
            task_type="images",
            is_async=True,
            callback_url=callback_url,
            data={"images": images, "det": det}
        )

        await task_queue.enqueue(task)

        return JSONResponse(
            status_code=220,
            content={
                "code": 220,
                "filename": ",".join(filenames),
                "taskid": task_id,
                "bizId": biz_id
            }
        )
    else:
        # 同步处理
        images = []
        for file in files:
            image = await load_image_from_upload(file)
            images.append(image)

        pages = await ocr_service.process_images_batch(images, det=det)

        return OCRResponse(
            code=200,
            filename=",".join(filenames),
            taskid=task_id,
            bizId=biz_id,
            pages=pages
        )
