from qka.brokers.server import qmt_server

qmt_server(
    account_id="your_account_id",
    mini_qmt_path=r"your_path_to_userdata_mini",
    host="127.0.0.1",
    port=8443,
    ssl_certfile="certs\\server.crt",
    ssl_keyfile="certs\\server.key",
    require_https=True,
    # api_key="",         # 如果不传则会随机生成一个
    # api_secret="",      # 如果不传则会随机生成一个
)
