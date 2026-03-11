# QKA - QMT 实盘交易助手

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/qka)](https://pypi.org/project/qka/)

**QKA** 聚焦 **QMT 实盘交易（客户端/服务端）**：
- 服务端：将 `xtquant` 交易接口封装为 FastAPI API
- 客户端：统一 `api(method_name, **params)` 调用
- 回调日志：提供委托、成交、错误等事件日志

## 安装

```bash
pip install qka
```

## 快速开始

### 1. 启动 QMT 交易服务器（HTTP）

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

### 2. 启动 QMT 交易服务器（HTTPS）

```python
from qka import QMTServer

server = QMTServer(
    account_id="YOUR_ACCOUNT_ID",
    mini_qmt_path="YOUR_QMT_PATH",
    host="0.0.0.0",
    port=8443,
    ssl_certfile="/path/to/server.crt",
    ssl_keyfile="/path/to/server.key",
    require_https=True,
)

server.start()
```

### 3. 使用客户端调用交易接口

```python
from qka import QMTClient
from xtquant import xtconstant

client = QMTClient(
    base_url="https://localhost:8443",
    token="SERVER_PRINTED_TOKEN",
    verify=False,  # 自签证书调试时可设为 False，生产环境请使用受信任证书并保持 True
)

assets = client.api("query_stock_asset")
print(assets)

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


## Windows HTTPS 部署教程（推荐）

以下步骤适用于 **Windows + miniQMT** 场景，按顺序执行即可。

### 步骤 1：准备目录

建议先创建固定目录，避免路径变更：

```powershell
mkdir C:\qka\certs -Force
mkdir C:\qka\run -Force
```

### 步骤 2：生成自签证书（开发/内网）

使用 OpenSSL 生成证书（若未安装 OpenSSL，可用 Git for Windows 自带或手动安装）。

```powershell
openssl req -x509 -nodes -newkey rsa:2048 `
  -keyout C:\qka\certs\server.key `
  -out C:\qka\certs\server.crt `
  -days 365 `
  -subj "/C=CN/ST=Beijing/L=Beijing/O=QKA/OU=Trading/CN=127.0.0.1"
```

> 说明：
> - 开发调试可用自签证书。
> - 生产环境请改为受信任 CA 证书，并在客户端开启证书校验。

### 步骤 3：编写服务端启动脚本

新建 `C:\qka\run\start_server.py`：

```python
from qka import QMTServer

server = QMTServer(
    account_id="YOUR_ACCOUNT_ID",
    mini_qmt_path=r"D:\miniQMT",  # 改成你的 miniQMT 路径
    host="0.0.0.0",
    port=8443,
    ssl_certfile=r"C:\qka\certs\server.crt",
    ssl_keyfile=r"C:\qka\certs\server.key",
    require_https=True,
    # 生产建议显式设置 token，便于运维管理
    token="REPLACE_WITH_A_STRONG_TOKEN",
)

server.start()
```

### 步骤 4：启动服务并获取 token

```powershell
python C:\qka\run\start_server.py
```

- 如果你没有在代码中显式传 `token`，启动日志会打印：`授权Token: ...`。
- 该 token 需要在客户端作为 `X-Token` 使用。

### 步骤 5：Windows 客户端调用（HTTPS）

新建 `C:\qka\run\client_demo.py`：

```python
from qka import QMTClient

client = QMTClient(
    base_url="https://127.0.0.1:8443",
    token="SERVER_PRINTED_OR_CONFIGURED_TOKEN",
    verify=False,  # 自签证书调试阶段可用；生产请改为 True 或 CA 路径
    timeout=10,
)

assets = client.api("query_stock_asset")
print(assets)
```

运行：

```powershell
python C:\qka\run\client_demo.py
```

### 步骤 6：连通性与鉴权检查（PowerShell）

1) 不带 token，预期 401：

```powershell
curl.exe -k -X POST https://127.0.0.1:8443/api/query_stock_asset -H "Content-Type: application/json" -d "{}"
```

2) 带 token，预期成功返回：

```powershell
curl.exe -k -X POST https://127.0.0.1:8443/api/query_stock_asset -H "Content-Type: application/json" -H "X-Token: YOUR_TOKEN" -d "{}"
```

### 步骤 7：Windows 生产建议

- 防火墙只放行 8443 到指定来源 IP，避免公网裸露。
- 证书与私钥设置访问权限，仅服务账号可读。
- 避免长期 `verify=False`。
- token 定期轮换，建议通过环境变量/密钥管理下发。

## 安全建议（实盘必须）

- 使用 `HTTPS`（`ssl_certfile` + `ssl_keyfile`），并在公网部署时开启 `require_https=True`。
- 显式传入高强度 `token`（建议密码管理器生成），不要复用旧 token。
- 通过防火墙/IP 白名单限制来源，仅开放给策略执行机。
- 把服务运行在内网或 VPN，不建议裸露公网。
- 增加交易风控（下单白名单、最大单笔/单日限额、撤单频率限制）。

## 核心模块

- `qka.brokers.server.QMTServer`：QMT 交易服务端
- `qka.brokers.client.QMTClient`：QMT 交易客户端
- `qka.brokers.trade.create_trader`：底层 `xtquant` 连接封装

## 免责声明

实盘交易存在风险，请在了解风险与合规要求的前提下使用。
