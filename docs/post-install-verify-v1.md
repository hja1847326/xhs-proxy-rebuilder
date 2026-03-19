# 安装后总验证 V1

## 目标

把安装后的检查和扩展路出口验证合成一份报告，减少人工东查西看。

## 脚本

- `scripts/post_install_verify.py`
- CLI：`xhs-proxy post-install-verify`

## 示例

```bash
python3 post_install_verify.py \
  --generated-dir ./generated-build \
  --endpoint http://ifconfig.me/ip
```

或：

```bash
xhs-proxy post-install-verify -- \
  --generated-dir ./generated-build \
  --endpoint http://ifconfig.me/ip
```
