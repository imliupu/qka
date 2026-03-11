"""
QKA - QMT 实盘交易框架

统一访问接口，聚焦 QMT 客户端/服务端功能。
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("qka")
except PackageNotFoundError:
    __version__ = "0.1.0"

from qka.brokers.client import QMTClient
from qka.brokers.server import QMTServer, qmt_server
from qka.brokers.trade import create_trader
from qka import brokers, utils

__all__ = [
    "QMTClient",
    "QMTServer",
    "qmt_server",
    "create_trader",
    "brokers",
    "utils",
]
