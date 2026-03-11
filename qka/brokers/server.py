"""
QKA交易服务器模块

提供基于FastAPI的QMT交易服务器，将QMT交易接口封装为RESTful API。
"""

import hmac
import inspect
import secrets
from typing import Any, Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
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
        token: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_keyfile: Optional[str] = None,
        require_https: bool = False,
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

        # 默认随机强token，避免机器码固定token可预测问题
        self.token = token if token else self.generate_token()
        print(f"\n授权Token: {self.token}\n")

    def generate_token(self) -> str:
        """生成随机高强度token。"""
        return secrets.token_urlsafe(48)

    def _tls_enabled(self) -> bool:
        return bool(self.ssl_certfile and self.ssl_keyfile)

    async def verify_token(self, x_token: str = Header(...)):
        """验证token依赖函数。"""
        if not hmac.compare_digest(x_token, self.token):
            raise HTTPException(status_code=401, detail="无效的Token")
        return x_token

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

        async def endpoint(request: request_model, token: str = Depends(self.verify_token)):
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
    token: Optional[str] = None,
    ssl_certfile: Optional[str] = None,
    ssl_keyfile: Optional[str] = None,
    require_https: bool = False,
):
    """快速创建并启动服务器。"""
    server = QMTServer(
        account_id=account_id,
        mini_qmt_path=mini_qmt_path,
        host=host,
        port=port,
        token=token,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
        require_https=require_https,
    )
    server.start()
