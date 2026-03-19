# curl 安装 V3

## 目标

把 `xhs-proxy` 推进到真正接近：

```bash
curl -fsSL https://.../install.sh | bash
```

的形态。

## 当前脚本

- `scripts/install_xhs_proxy_from_url.sh`

它支持：

```bash
bash scripts/install_xhs_proxy_from_url.sh https://example.com/xhs-proxy-cli.tar.gz
```

或者：

```bash
XHS_PROXY_CLI_URL=https://example.com/xhs-proxy-cli.tar.gz \
  bash scripts/install_xhs_proxy_from_url.sh
```

## 当前意义

现在已经具备：
- CLI tar.gz 打包
- 从 tar.gz 安装
- 从 URL 下载 tar.gz 再安装

也就是说，只要你后面把 `xhs-proxy-cli.tar.gz` 放到一个公网 URL，
这条命令链就能工作。

## 还差最后一层

如果想真正做到：

```bash
curl -fsSL https://your-domain/install-xhs-proxy.sh | bash
```

那还需要：
- 把本脚本本身托管到公网
- 在脚本里固定 `XHS_PROXY_CLI_URL`
- 或者让脚本根据版本自动拼下载地址

## 当前推荐测试方式

先本地启动一个临时 HTTP 服务验证：

```bash
cd dist
python3 -m http.server 8000
```

然后另一终端执行：

```bash
bash scripts/install_xhs_proxy_from_url.sh http://127.0.0.1:8000/xhs-proxy-cli-test.tar.gz
```
