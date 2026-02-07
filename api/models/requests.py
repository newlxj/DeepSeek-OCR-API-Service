"""
请求数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class OCRBaseRequest(BaseModel):
    """OCR请求基础模型"""
    biz_id: str = Field(..., description="业务ID")
    is_async: bool = Field(False, description="是否异步处理")
    callback_url: Optional[str] = Field(None, description="回调地址，异步模式必填")
    det: bool = Field(False, description="是否输出检测位置信息")


class PDFRequest(OCRBaseRequest):
    """PDF OCR请求"""
    skip_pages: Optional[str] = Field(None, description="跳过的页码，逗号分隔，如 '0,2,5'")
    limit_pages: Optional[int] = Field(None, description="限制处理页数")


class ImageRequest(OCRBaseRequest):
    """单图OCR请求"""
    pass


class ImagesRequest(OCRBaseRequest):
    """批量图片OCR请求"""
    pass
