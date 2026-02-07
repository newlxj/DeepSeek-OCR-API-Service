"""
OCR处理服务
"""
import io
import re
from typing import List, Optional
from PIL import Image
import fitz

from process.image_process import DeepseekOCR2Processor
from config import PROMPT, CROP_MODE
from .model_manager import model_manager


class OCRService:
    """OCR处理服务"""

    def __init__(self):
        self.model_manager = model_manager
        self.processor = DeepseekOCR2Processor()

    async def process_image(
        self,
        image: Image.Image,
        det: bool = False
    ) -> str:
        """
        处理单张图片

        Args:
            image: PIL.Image对象
            det: 是否输出检测位置信息

        Returns:
            str: OCR结果（Markdown格式）
        """
        # 使用批量处理，单张图片作为批量大小为1的特例
        results = await self.process_images_batch([image], det=det)
        return results[0] if results else ""

    async def process_images_batch(
        self,
        images: List[Image.Image],
        det: bool = False
    ) -> List[str]:
        """
        批量处理图片

        Args:
            images: PIL.Image对象列表
            det: 是否输出检测位置信息

        Returns:
            List[str]: OCR结果列表（Markdown格式）
        """
        llm = self.model_manager.get_llm()
        sampling_params = self.model_manager.get_sampling_params()

        # 预处理
        batch_inputs = []
        for image in images:
            image_features = self.processor.tokenize_with_images(
                images=[image],
                bos=True,
                eos=True,
                cropping=CROP_MODE
            )
            batch_inputs.append({
                "prompt": PROMPT,
                "multi_modal_data": {"image": image_features}
            })

        # 批量推理
        outputs_list = llm.generate(batch_inputs, sampling_params=sampling_params)

        # 后处理
        results = []
        for output in outputs_list:
            content = output.outputs[0].text
            # 总是移除 end of sentence 标记
            content = content.replace('<｜end▁of▁sentence｜>', '')
            if not det:
                content = self._remove_det_tags(content)
            results.append(content)

        return results

    async def process_pdf(
        self,
        pdf_path: str,
        skip_pages: Optional[List[int]] = None,
        limit_pages: Optional[int] = None,
        det: bool = False
    ) -> List[str]:
        """
        处理PDF文件

        Args:
            pdf_path: PDF文件路径
            skip_pages: 跳过的页码列表
            limit_pages: 限制处理页数
            det: 是否输出检测位置信息

        Returns:
            List[str]: 每页的OCR结果（Markdown格式）
        """
        # PDF转图像
        images = self._pdf_to_images(pdf_path)

        # 过滤页面
        if skip_pages:
            images = [img for i, img in enumerate(images) if i not in skip_pages]
        if limit_pages:
            images = images[:limit_pages]

        # 批量处理
        results = await self.process_images_batch(images, det=det)

        return results

    def _pdf_to_images(self, pdf_path: str, dpi: int = 144) -> List[Image.Image]:
        """
        PDF转高分辨率图像

        Args:
            pdf_path: PDF文件路径
            dpi: 分辨率

        Returns:
            List[Image.Image]: 图像列表
        """
        images = []
        pdf_document = fitz.open(pdf_path)

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)

        pdf_document.close()
        return images

    def _remove_det_tags(self, text: str) -> str:
        """
        移除检测标签

        当det=false时，移除所有 <|ref|>...<|/ref|><|det|>...<|/det|> 标签
        对于图像标签，保留图片引用；对于其他标签，完全移除

        Args:
            text: 带检测标签的文本

        Returns:
            str: 纯文本内容
        """
        # 首先移除 end of sentence 标记
        text = text.replace('<｜end▁of▁sentence｜>', '')

        # 匹配所有 ref-det 标签
        pattern = r'<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>'
        matches = re.findall(pattern, text, re.DOTALL)

        for match in matches:
            ref_text = match[0]  # <|ref|> 和 <|/ref|> 之间的内容
            det_text = match[1]  # <|det|> 和 <|/det|> 之间的内容
            full_match = f'<|ref|>{ref_text}<|/ref|><|det|>{det_text}<|/det|>'

            # 检查是否是图像标签
            if '<|ref|>image<|/ref|>' in full_match:
                # 图像标签：移除位置信息，但保留结构（这里简化为移除）
                text = text.replace(full_match, '')
            else:
                # 其他标签：完全移除整个标签（包括标签内的文本）
                text = text.replace(full_match, '')

        # 清理多余换行和特殊字符
        text = text.replace('\\coloneqq', ':=').replace('\\eqqcolon', '=:')
        text = re.sub(r'\n{4,}', '\n\n', text)
        # 清理可能留下的空行
        text = re.sub(r'^\s*\n', '', text, flags=re.MULTILINE)

        return text
