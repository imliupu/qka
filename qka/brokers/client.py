"""QKA交易客户端模块。"""

import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional, Union

import requests

from qka.utils.logger import logger


class QMTClient:
    """QMT交易客户端类。"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: float = 10.0,
        verify: Union[bool, str] = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if not api_key or not api_secret:
            raise ValueError("必须同时提供 api_key 和 api_secret")

        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self.verify = verify

    def _generate_sign(self, timestamp: str, nonce: str, body_text: str) -> str:
        payload = f"{self.api_key}\n{timestamp}\n{nonce}\n{body_text}"
        return hmac.new(
            self.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _build_headers(self, body_text: str) -> Dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)
        sign = self._generate_sign(timestamp, nonce, body_text)
        return {
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Sign": sign,
            "Content-Type": "application/json",
        }

    def api(self, method_name: str, **params) -> Any:
        """通用调用接口方法。"""
        try:
            payload = params or {}
            body_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            response = self.session.post(
                f"{self.base_url}/api/{method_name}",
                data=body_text.encode("utf-8"),
                headers=self._build_headers(body_text),
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
