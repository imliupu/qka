"""
QKA交易客户端模块

提供QMT交易服务器的客户端接口，支持远程调用交易功能。
"""

from typing import Any, Dict, Optional, Union

import requests

from qka.utils.logger import logger


class QMTClient:
    """QMT交易客户端类。"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: Optional[str] = None,
        timeout: float = 10.0,
        verify: Union[bool, str] = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if not token:
            raise ValueError("必须提供访问令牌(token)")

        self.token = token
        self.timeout = timeout
        self.verify = verify
        self.headers = {"X-Token": self.token}

    def api(self, method_name: str, **params) -> Any:
        """通用调用接口方法。"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/{method_name}",
                json=params or {},
                headers=self.headers,
                timeout=self.timeout,
                verify=self.verify,
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                raise Exception(f"API调用失败: {result.get('detail')}")

            return result.get("data")
        except Exception as e:
            logger.error(f"调用 {method_name} 失败: {str(e)}")
            raise
