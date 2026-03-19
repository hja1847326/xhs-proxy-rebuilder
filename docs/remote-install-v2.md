# 远程一键安装 V2

## 目标

把 `xhs-proxy` 推进到“可从 tar.gz 包或 URL 安装”的结构。

## 新增脚本

- `scripts/package_cli_bundle.py`：打 CLI 分发包
- `scripts/install_xhs_proxy_remote.sh`：从本地 tar.gz 或 URL 安装

## 典型流程

### 1. 打 CLI 包
```bash
./xhs-proxy package-cli
```

默认产物：
- `dist/xhs-proxy-cli.tar.gz`

### 2. 本地文件安装
```bash
bash scripts/install_xhs_proxy_remote.sh dist/xhs-proxy-cli.tar.gz
```

### 3. URL 安装（结构已支持）
```bash
bash scripts/install_xhs_proxy_remote.sh https://example.com/xhs-proxy-cli.tar.gz
```

## 当前意义

现在即使还没挂公网 URL，安装结构已经准备好了：
- 可先打 tar.gz
- 可从 tar.gz 安装
- 将来换成 URL，只是换传输来源，不是重写安装逻辑
- CLI 包已包含 `apply_network_plan.py` / `apply_netns_expansion.py` / `validate_netns_expansion.py` / `healthcheck_install.py` / `post_install_verify.py`
- release bundle 可选直接携带 `gost`，减少远端手工准备步骤

## 当前限制

- 还没提供真实公网下载地址
- 还没做 curl 直管道最终体验
