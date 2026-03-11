# QKA - QMT 实盘交易助手

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/qka)](https://pypi.org/project/qka/)

**QKA** 现在聚焦于 **QMT 实盘交易（客户端/服务端）**：
- 服务端：将 `xtquant` 交易接口封装为 FastAPI API
- 客户端：统一 `api(method_name, **params)` 调用
- 回调日志：提供委托、成交、错误等事件日志

## 安装

```bash
pip install qka
```

## 快速开始

### 1. 启动 QMT 交易服务器

```python
from qka import QMTServer

server = QMTServer(
    account_id="YOUR_ACCOUNT_ID",
    mini_qmt_path="YOUR_QMT_PATH",
    host="0.0.0.0",
    port=8000,
)

server.start()
```

启动后会输出 token，客户端调用时需要放在 `X-Token`。

### 2. 使用客户端调用交易接口

```python
from qka import QMTClient
from xtquant import xtconstant

client = QMTClient(
    base_url="http://localhost:8000",
    token="SERVER_PRINTED_TOKEN",
)

# 查询资产
assets = client.api("query_stock_asset")
print(assets)

# 下单
result = client.api(
    "order_stock",
    stock_code="600000.SH",
    order_type=xtconstant.STOCK_BUY,
    order_volume=100,
    price_type=xtconstant.FIX_PRICE,
    price=10.5,
)
print(result)
```

## 核心模块

- `qka.brokers.server.QMTServer`：QMT 交易服务端
- `qka.brokers.client.QMTClient`：QMT 交易客户端
- `qka.brokers.trade.create_trader`：底层 `xtquant` 连接封装

## 免责声明

实盘交易存在风险，请在了解风险与合规要求的前提下使用。
