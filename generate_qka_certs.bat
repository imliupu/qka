@echo off
setlocal

set "certDir=.\certs"

echo 开始生成证书...

if not exist "%certDir%" mkdir "%certDir%"
cd /d "%certDir%"

rem 1) 生成 CA 密钥和证书
openssl genrsa -out ca.key 4096
if errorlevel 1 exit /b
openssl req -x509 -new -nodes -key ca.key -days 3650 -sha256 -out ca.pem -config ..\openssl.cnf -extensions v3_ca
if errorlevel 1 exit /b

rem 2) 生成服务器密钥和证书签名请求
openssl genrsa -out server.key 2048
if errorlevel 1 exit /b
openssl req -new -key server.key -out server.csr -config ..\openssl.cnf -reqexts v3_req
if errorlevel 1 exit /b

rem 3) 用 CA 签署服务器证书
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out server.crt -days 365 -sha256 -extfile ..\openssl.cnf -extensions v3_server
if errorlevel 1 exit /b

rem 4) 验证证书
openssl verify -CAfile ca.pem server.crt
if errorlevel 1 exit /b

echo 完成。输出文件位于 .\certs
endlocal
