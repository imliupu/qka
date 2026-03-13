"""
QKA交易服务器模块

提供基于FastAPI的QMT交易服务器，将QMT交易接口封装为RESTful API。
"""

import hashlib
import hmac
import inspect
import secrets
import time
from typing import Any, Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

from qka.brokers.trade import create_trader


class QMTServer:
    """
    QMT交易服务器类。

    将QMT交易接口封装为RESTful API，支持远程调用交易功能。
    """

    def __init__(
        self,
        account_id: str,
        mini_qmt_path: str,
        host: str = "0.0.0.0",
        port: int = 8000,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_keyfile: Optional[str] = None,
        require_https: bool = False,
        timestamp_tolerance_seconds: int = 300,
    ):
        self.account_id = account_id
        self.mini_qmt_path = mini_qmt_path
        self.host = host
        self.port = port
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile
        self.require_https = require_https
        self.app = FastAPI()
        self.trader = None
        self.account = None
        self.timestamp_tolerance_seconds = timestamp_tolerance_seconds
        self._used_nonces: Dict[str, int] = {}

        # 默认随机生成 API 凭证，避免固定弱口令
        self.api_key = api_key if api_key else self.generate_api_key()
        self.api_secret = api_secret if api_secret else self.generate_api_secret()
        print(f"\n授权API Key: {self.api_key}\n")
        print(f"\n授权API Secret: {self.api_secret}\n")

    def generate_api_key(self) -> str:
        """生成随机 API Key。"""
        return secrets.token_urlsafe(24)

    def generate_api_secret(self) -> str:
        """生成随机 API Secret。"""
        return secrets.token_urlsafe(48)

    def _build_sign_payload(self, api_key: str, timestamp: str, nonce: str, body: bytes) -> str:
        """构建待签名字符串。"""
        body_text = body.decode("utf-8") if body else ""
        return f"{api_key}\n{timestamp}\n{nonce}\n{body_text}"

    def _cleanup_nonce_cache(self, now: int):
        """清理过期 nonce。"""
        expired = [
            nonce
            for nonce, nonce_time in self._used_nonces.items()
            if now - nonce_time > self.timestamp_tolerance_seconds
        ]
        for nonce in expired:
            self._used_nonces.pop(nonce, None)

    def _tls_enabled(self) -> bool:
        return bool(self.ssl_certfile and self.ssl_keyfile)

    async def verify_signature(
        self,
        request: Request,
        x_api_key: str = Header(...),
        x_timestamp: str = Header(...),
        x_nonce: str = Header(...),
        x_sign: str = Header(...),
    ):
        """验证 APIKEY + TIMESTAMP + NONCE + SIGN。"""
        if not hmac.compare_digest(x_api_key, self.api_key):
            raise HTTPException(status_code=401, detail="无效的API Key")

        try:
            timestamp_int = int(x_timestamp)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="无效的Timestamp") from exc

        now = int(time.time())
        if abs(now - timestamp_int) > self.timestamp_tolerance_seconds:
            raise HTTPException(status_code=401, detail="Timestamp已过期")

        self._cleanup_nonce_cache(now)
        if x_nonce in self._used_nonces:
            raise HTTPException(status_code=401, detail="重复的Nonce")

        body = await request.body()
        payload = self._build_sign_payload(x_api_key, x_timestamp, x_nonce, body)
        expected_sign = hmac.new(
            self.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(x_sign, expected_sign):
            raise HTTPException(status_code=401, detail="无效的Sign")

        self._used_nonces[x_nonce] = now
        return True

    def init_trader(self):
        """初始化交易对象。"""
        self.trader, self.account = create_trader(self.account_id, self.mini_qmt_path)

    def convert_to_dict(self, obj) -> Dict[str, Any]:
        """将结果转换为可序列化结构。"""
        if isinstance(obj, (int, float, str, bool)):
            return obj
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, (list, tuple)):
            return [self.convert_to_dict(item) for item in obj]
        if hasattr(obj, "__dir__"):
            attrs = obj.__dir__()
            public_attrs = {
                attr: getattr(obj, attr)
                for attr in attrs
                if not attr.startswith("_") and not callable(getattr(obj, attr))
            }
            return public_attrs
        return str(obj)

    def convert_method_to_endpoint(self, method_name: str, method):
        """将 XtQuantTrader 方法转换为 FastAPI 端点。"""
        sig = inspect.signature(method)
        param_names = list(sig.parameters.keys())

        class_fields = {"__annotations__": {}}
        for param in param_names:
            if param in ["self", "account"]:
                continue
            class_fields["__annotations__"][param] = Any
            class_fields[param] = None

        request_model = type(f"{method_name}Request", (BaseModel,), class_fields)

        async def endpoint(request: request_model, _: bool = Depends(self.verify_signature)):
            try:
                params = request.dict(exclude_unset=True)
                if "account" in param_names:
                    params["account"] = self.account
                result = getattr(self.trader, method_name)(**params)
                return {"success": True, "data": self.convert_to_dict(result)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        self.app.post(f"/api/{method_name}")(endpoint)

    def setup_routes(self):
        """设置所有路由。"""
        trader_methods = inspect.getmembers(
            self.trader.__class__,
            predicate=lambda x: inspect.isfunction(x) or inspect.ismethod(x),
        )

        excluded_methods = {
            "__init__",
            "__del__",
            "register_callback",
            "start",
            "stop",
            "connect",
            "sleep",
            "run_forever",
            "set_relaxed_response_order_enabled",
        }

        for method_name, method in trader_methods:
            if not method_name.startswith("_") and method_name not in excluded_methods:
                self.convert_method_to_endpoint(method_name, method)

    def start(self):
        """启动服务器。"""
        if self.require_https and not self._tls_enabled():
            raise ValueError("require_https=True 时必须同时提供 ssl_certfile 和 ssl_keyfile")

        self.init_trader()
        self.setup_routes()
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            ssl_certfile=self.ssl_certfile,
            ssl_keyfile=self.ssl_keyfile,
        )


def qmt_server(
    account_id: str,
    mini_qmt_path: str,
    host: str = "0.0.0.0",
    port: int = 8000,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    ssl_certfile: Optional[str] = None,
    ssl_keyfile: Optional[str] = None,
    require_https: bool = False,
    timestamp_tolerance_seconds: int = 300,
):
    """快速创建并启动服务器。"""
    server = QMTServer(
        account_id=account_id,
        mini_qmt_path=mini_qmt_path,
        host=host,
        port=port,
        api_key=api_key,
        api_secret=api_secret,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
        require_https=require_https,
        timestamp_tolerance_seconds=timestamp_tolerance_seconds,
    )
    server.start()
