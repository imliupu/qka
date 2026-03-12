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
    api_key="SERVER_PRINTED_API_KEY",
    api_secret="SERVER_PRINTED_API_SECRET",
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
    # 生产建议显式设置 api_key/api_secret，便于运维管理
    api_key="REPLACE_WITH_API_KEY",
    api_secret="REPLACE_WITH_API_SECRET",
)

server.start()
```

### 步骤 4：启动服务并获取 API 凭证

```powershell
python C:\qka\run\start_server.py
```

- 如果你没有在代码中显式传 `api_key/api_secret`，启动日志会打印：`授权API Key` 和 `授权API Secret`。
- 客户端每次请求会自动生成 `X-Timestamp`、`X-Nonce` 并计算 `X-Sign`，你只需提供 `api_key/api_secret`。

### 步骤 5：Windows 客户端调用（HTTPS）

新建 `C:\qka\run\client_demo.py`：

```python
from qka import QMTClient

client = QMTClient(
    base_url="https://127.0.0.1:8443",
    api_key="SERVER_PRINTED_OR_CONFIGURED_API_KEY",
    api_secret="SERVER_PRINTED_OR_CONFIGURED_API_SECRET",
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

1) 缺少签名头，预期 401：

```powershell
curl.exe -k -X POST https://127.0.0.1:8443/api/query_stock_asset -H "Content-Type: application/json" -d "{}"
```

2) 使用 `QMTClient`（自动签名）调用，预期成功返回。

### 步骤 7：Windows 生产建议

- 防火墙只放行 8443 到指定来源 IP，避免公网裸露。
- 证书与私钥设置访问权限，仅服务账号可读。
- 避免长期 `verify=False`。
- API Secret 定期轮换，建议通过环境变量/密钥管理下发。

## 安全建议（实盘必须）

- 使用 `HTTPS`（`ssl_certfile` + `ssl_keyfile`），并在公网部署时开启 `require_https=True`。
- 显式传入高强度 `api_key/api_secret`（建议密码管理器生成），不要复用旧密钥。
- 通过防火墙/IP 白名单限制来源，仅开放给策略执行机。
- 把服务运行在内网或 VPN，不建议裸露公网。
- 增加交易风控（下单白名单、最大单笔/单日限额、撤单频率限制）。

## 核心模块

- `qka.brokers.server.QMTServer`：QMT 交易服务端
- `qka.brokers.client.QMTClient`：QMT 交易客户端
- `qka.brokers.trade.create_trader`：底层 `xtquant` 连接封装

## 免责声明

实盘交易存在风险，请在了解风险与合规要求的前提下使用。

## Windows 生产环境 HTTPS 部署教程（追加）

> 本节是**生产环境**专用教程，基于上文 Windows 教程进一步加固。建议先完成上文“Windows HTTPS 部署教程”再执行本节。

### 0. 目标与架构建议（先定方案）

生产建议采用以下最小架构：

1. **QMT Server 主机（Windows）**：仅运行 miniQMT + qka 服务。
2. **策略执行主机**：只作为客户端调用 `https://QMT_SERVER:8443`。
3. **网络隔离**：QMT Server 不直接暴露公网，只允许固定来源 IP（策略机/跳板机/VPN 网段）。

### 1. 生产目录规划与权限

建议固定目录（示例）：

```powershell
mkdir C:\qka\certs -Force
mkdir C:\qka\run -Force
mkdir C:\qka\logs -Force
```

将私钥和证书放在 `C:\qka\certs`，并确保：

- `server.key` 仅运行服务的账号可读。
- 非管理员/普通用户无读取权限。

### 2. 证书方案（生产推荐）

优先级建议：

1. **企业内网 CA 证书（推荐）**
2. 公网受信任 CA 证书（若你必须公网或跨网访问）
3. 自签证书（仅临时，不建议长期生产）

#### 3）自签证书（仅临时，不建议长期生产）

> 以下为你提供的流程，已改成 **Windows PowerShell** 可直接执行版本。
> 若遇到 `openssl.cnf` 报错，先看下一节“### 3. 解决 Windows OpenSSL openssl.cnf 报错”。

先给你一个一键脚本（推荐）：

```powershell
# 在仓库根目录执行
powershell -ExecutionPolicy Bypass -File .\generate_qka_certs.ps1
```

脚本会自动：

- 生成合法 CA（含 `CA:TRUE` / `keyCertSign`）
- 生成服务端证书（含 `SAN` 与 `serverAuth`）
- 最后执行 `openssl verify` 验证证书链

脚本位置：`generate_qka_certs.ps1`。

如果你更希望手工执行，再用下面分步命令：

1. 创建 CA（根证书）

```powershell
cd C:\qka\certs

# 生成 CA 私钥
openssl genrsa -out ca.key 4096

# 生成 CA 证书（有效期 10 年）
openssl req -x509 -new -nodes `
  -key ca.key `
  -sha256 -days 3650 `
  -out ca.pem
```

生成结果：

- `ca.key`（CA 私钥）
- `ca.pem`（CA 证书）

2. 创建服务器证书请求材料

```powershell
cd C:\qka\certs

# 生成服务器私钥
openssl genrsa -out server.key 2048

# 生成 CSR（证书签名请求）
openssl req -new -key server.key -out server.csr
```

3. 用 CA 签发服务器证书

```powershell
cd C:\qka\certs

openssl x509 -req `
  -in server.csr `
  -CA ca.pem `
  -CAkey ca.key `
  -CAcreateserial `
  -out server.crt `
  -days 365 `
  -sha256
```

生成结果：

- `server.crt`
- `server.key`

4. 服务端与客户端如何使用

- 服务端 `QMTServer` 使用：
  - `ssl_certfile="C:\\qka\\certs\\server.crt"`
  - `ssl_keyfile="C:\\qka\\certs\\server.key"`
- 客户端请开启证书校验并信任 CA：
  - `verify="C:\\qka\\certs\\ca.pem"`

> 提醒：自签证书适合内网临时联调。正式生产建议切换企业 CA 或公网受信任 CA。

证书要求：

- `CN/SAN` 必须包含客户端实际访问的域名/IP。
- 有效期、续期计划、证书吊销策略需要提前制定。

### 3. 解决 Windows OpenSSL `openssl.cnf` 报错（你遇到的典型问题）

当出现：

`Can't open "C:\Program Files\Common Files\ssl\/openssl.cnf" for reading`

说明 OpenSSL 找不到配置文件。可选修复方式：

#### 方式 A：设置环境变量（推荐）

```powershell
$env:OPENSSL_CONF="C:\Program Files\OpenSSL-Win64\bin\openssl.cfg"
```

> 路径按你本机 OpenSSL 实际安装位置调整；可先 `where openssl` 确认。

#### 方式 B：命令中显式指定配置文件

```powershell
openssl req -config "C:\Program Files\OpenSSL-Win64\bin\openssl.cfg" -x509 -nodes -newkey rsa:2048 `
  -keyout C:\qka\certs\server.key `
  -out C:\qka\certs\server.crt `
  -days 365 `
  -subj "/C=CN/ST=Beijing/L=Beijing/O=QKA/OU=Trading/CN=qmt.example.local"
```

### 4. 生产服务端启动脚本（环境变量读取敏感信息）

新建 `C:\qka\run\start_server_prod.py`：

```python
import os
from qka import QMTServer

account_id = os.environ["QKA_ACCOUNT_ID"]
mini_qmt_path = os.environ["QKA_MINI_QMT_PATH"]
api_key = os.environ["QKA_API_KEY"]
api_secret = os.environ["QKA_API_SECRET"]

server = QMTServer(
    account_id=account_id,
    mini_qmt_path=mini_qmt_path,
    host="0.0.0.0",
    port=8443,
    ssl_certfile=r"C:\qka\certs\server.crt",
    ssl_keyfile=r"C:\qka\certs\server.key",
    require_https=True,
    api_key=api_key,
    api_secret=api_secret,
)

server.start()
```

设置环境变量（当前 PowerShell 会话）：

```powershell
$env:QKA_ACCOUNT_ID="YOUR_ACCOUNT_ID"
$env:QKA_MINI_QMT_PATH="D:\miniQMT"
$env:QKA_API_KEY="REPLACE_WITH_API_KEY"
$env:QKA_API_SECRET="REPLACE_WITH_A_LONG_RANDOM_SECRET"
python C:\qka\run\start_server_prod.py
```

> 生产中不要把 api_secret 硬编码到仓库文件。

### 5. 防火墙最小开放策略（必须）

仅允许可信来源访问 8443。示例（将 `10.10.10.20` 替换为策略机 IP）：

```powershell
New-NetFirewallRule -DisplayName "QKA HTTPS Inbound" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8443 -RemoteAddress 10.10.10.20
```

若存在旧的 8000 明文端口策略，请删除或禁用对应规则。

### 6. 生产客户端示例（启用证书校验）

```python
from qka import QMTClient

client = QMTClient(
    base_url="https://qmt.example.local:8443",
    api_key="PROD_API_KEY",
    api_secret="PROD_API_SECRET",
    verify=r"C:\qka\certs\ca_bundle.pem",  # 或 True（系统信任链）
    timeout=10,
)

print(client.api("query_stock_asset"))
```

注意：

- 生产禁止长期 `verify=False`。
- 若是内网 CA，客户端必须安装/信任对应 CA。

### 7. 生产验收检查清单（逐项打勾）

1. 使用 `https://` 地址可访问服务。
2. 缺少签名头请求返回 401。
3. 带正确签名请求返回业务结果。
4. `verify=True` 或 CA 校验模式下调用成功。
5. 错误签名、重复 Nonce、错误来源 IP 被拒绝。
6. 证书过期时间已登记到监控/日历（提前 30 天提醒）。

### 8. 运行维护（建议）

- **API Secret 轮换**：按周/月轮换，并在策略端同步更新。
- **证书轮换**：至少年更，过期前完成灰度替换。
- **日志审计**：记录调用来源、接口名、时间、结果摘要（避免泄露敏感字段）。
- **灾备演练**：定期验证服务重启、证书替换、API Secret 轮换流程。

### 9. 常见故障快速定位（生产高频）

1. `SSL: CERTIFICATE_VERIFY_FAILED`
   - 客户端未信任签发 CA；或域名与证书不匹配。
2. `401` 鉴权失败
   - API Key 不一致、Sign 算法/请求体不一致、Timestamp 过期、Nonce 重复。
3. 连接超时
   - 防火墙未放行、端口未监听、证书路径错误导致服务启动失败。
4. OpenSSL 配置文件错误
   - 按“第 3 节”设置 `OPENSSL_CONF` 或 `-config` 参数。
