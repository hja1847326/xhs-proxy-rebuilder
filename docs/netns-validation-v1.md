# 扩展路验证 V1

## 目标

对 `4+N` 中的 txt 扩展路做两层验证：

1. `netns` 内直连外网是否拿到目标公网出口
2. 通过 SOCKS5 代理访问验证地址时，是否拿到同一公网出口

## 脚本

- `scripts/validate_netns_expansion.py`
- CLI 子命令：`xhs-proxy validate-netns`

## 示例

### 直接验证 bundle 中的扩展计划
```bash
python3 validate_netns_expansion.py \
  --plan ./netns-expansion-plan.json \
  --endpoint http://ifconfig.me/ip
```

### 使用 CLI
```bash
xhs-proxy validate-netns -- \
  --plan ./netns-expansion-plan.json \
  --endpoint http://ifconfig.me/ip
```

## 验证建议

- 优先使用 `http://ifconfig.me/ip`
- 不要把 `api.ipify.org` 当唯一标准
- 如果公网监听 IP 与 namespace 内 bind IP 不同，可切换：

```bash
python3 validate_netns_expansion.py \
  --plan ./netns-expansion-plan.json \
  --proxy-host-field public_listen_ip
```
