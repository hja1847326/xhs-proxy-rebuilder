# Smoke Tests V1

## 目标

用少量已知好/坏样例，快速确认校验器和主流程没有被后续改动搞残。

## 当前样例

### 错误样例
- `tests/invalid-duplicate-port.yaml`
- `tests/invalid-duplicate-username.yaml`
- `tests/invalid-profile-strategy.yaml`

### 正常样例
- `inventory/generated-10ip.yaml`
- `profiles/huaweicloud-10ip.yaml`

## 运行方式

```bash
python3 scripts/smoke_tests.py
```

## 当前覆盖

- 重复端口应失败
- 重复用户名应失败
- 非法 strategy 应失败
- 正常 inventory + profile 应通过
