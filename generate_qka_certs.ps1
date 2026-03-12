$ErrorActionPreference = "Stop"

$certDir = ".\certs"

Write-Host "开始生成证书..."

cd $certDir

# 1) CA
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -days 3650 -sha256 `
  -out ca.pem -config ..\openssl.cnf -extensions v3_ca

# 2) server key + csr
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr `
  -config ..\openssl.cnf -reqexts v3_req

# 3) sign server cert
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial `
  -out server.crt -days 365 -sha256 `
  -extfile ..\openssl.cnf -extensions v3_server

# 4) verify
openssl verify -CAfile ca.pem server.crt

Write-Host "完成。输出文件位于 .\certs" -ForegroundColor Green
