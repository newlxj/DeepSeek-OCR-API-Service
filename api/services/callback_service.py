"""
HTTP回调服务
"""
import httpx
from typing import Dict, Any, Optional
import logging

from ..config import API_CONFIG

logger = logging.getLogger(__name__)


class CallbackService:
    """回调服务"""

    def __init__(self, timeout: Optional[int] = None):
        """
        初始化回调服务

        Args:
            timeout: 超时时间（秒），默认使用配置文件中的值
        """
        self.timeout = timeout or API_CONFIG.callback_timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        return self.client

    async def send_callback(
        self,
        url: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        发送回调通知

        Args:
            url: 回调URL
            data: 回调数据

        Returns:
            bool: 是否成功
        """
        try:
            client = await self._get_client()
            response = await client.post(url, json=data)
            response.raise_for_status()
            logger.info(f"Callback sent successfully to {url}")
            return True
        except Exception as e:
            logger.error(f"Callback failed for {url}: {str(e)}")
            return False

    async def close(self) -> None:
        """关闭客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None
