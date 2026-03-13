from xtquant import xttrader
from xtquant.xttype import StockAccount
import random

# 1. 初始化 QMT 交易对象
# minipath: 交易终端数据路径与端口号
# session_id: 随机生成一个会话ID，用于区分不同的连接实例
min_path = r'E:\中金财富QMT个人版交易端\userdata_mini'
session_id = int(random.randint(100000, 999999))
xt_trader = xttrader.XtQuantTrader(min_path, session_id)

# 2. 启动交易线程并开始连接
xt_trader.start()
connect_result = xt_trader.connect()

# 3. 判断连接是否成功
if connect_result == 0:
    print("连接成功")
else:
    print("连接失败，请检查路径或QMT客户端状态")


account = StockAccount('your_account_id') 
# 调用查询接口，传入账户对象
asset_info = xt_trader.query_stock_asset(account)

# 从返回的asset_info对象中提取余额信息
if asset_info:
    print(f"总资产: {asset_info.total_asset}")
    print(f"可用金额: {asset_info.cash}")
    print(f"冻结金额: {asset_info.frozen_cash}")
    print(f"持仓市值: {asset_info.market_value}")
else:
    print("查询失败，请检查账户或网络连接")
