from qka import QMTClient

client = QMTClient(
    base_url="https://127.0.0.1:8443",
    api_key="",         # 和服务器的保持一致
    api_secret="",      # 和服务器的保持一致
    verify=r"ca.pem",  # 自签证书调试阶段可用；生产请改为 True 或 CA 路径
    timeout=10,
)

assets = client.api("query_stock_asset")
print(assets)
