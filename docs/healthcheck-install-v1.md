# 安装后健康检查 V1

## 目标

安装完成后，快速确认：

- `xray` 服务是否在运行
- 各扩展 `netns` 是否存在关键网络状态
- 对应 `xhs-gost-nsXXXX.service` 是否在运行
- 默认路由 / DNS 文件是否存在

## 脚本

- `scripts/healthcheck_install.py`
- CLI：`xhs-proxy healthcheck-install`

## 示例

```bash
python3 healthcheck_install.py --generated-dir ./generated-build
```

或：

```bash
xhs-proxy healthcheck-install -- --generated-dir ./generated-build
```
