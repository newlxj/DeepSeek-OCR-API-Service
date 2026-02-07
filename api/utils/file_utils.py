"""
文件处理工具
"""
import io
import os
import uuid
from typing import Optional
from fastapi import UploadFile
from PIL import Image, ImageOps


async def load_image_from_upload(file: UploadFile) -> Image.Image:
    """
    从上传文件加载图像

    Args:
        file: FastAPI UploadFile对象

    Returns:
        PIL.Image对象

    Raises:
        FileProcessingException: 文件处理失败
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # 自动修正EXIF方向
        corrected_image = ImageOps.exif_transpose(image)

        return corrected_image

    except Exception as e:
        from ..exceptions import FileProcessingException
        raise FileProcessingException(f"Failed to load image: {str(e)}")


async def save_upload_file_tmp(file: UploadFile) -> str:
    """
    保存上传文件到临时目录

    Args:
        file: FastAPI UploadFile对象

    Returns:
        临时文件路径
    """
    # 创建临时文件名
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tmp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, temp_filename)

    # 保存文件
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    return temp_path


def cleanup_temp_file(file_path: str) -> None:
    """
    清理临时文件

    Args:
        file_path: 文件路径
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # 静默处理清理失败
        pass


def validate_image_file(filename: str) -> bool:
    """
    验证是否为支持的图像文件

    Args:
        filename: 文件名

    Returns:
        是否为支持的图像格式
    """
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    ext = os.path.splitext(filename)[1].lower()
    return ext in valid_extensions


def validate_pdf_file(filename: str) -> bool:
    """
    验证是否为PDF文件

    Args:
        filename: 文件名

    Returns:
        是否为PDF文件
    """
    return os.path.splitext(filename)[1].lower() == ".pdf"
