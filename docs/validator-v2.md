# Validator V2

## 目标

把校验从“能解析”升级成“配置是否靠谱”。

## 新增检查

### Inventory 侧
- 重复 proxy name
- 重复 port
- 重复 listen endpoint（IP:port）
- 重复 username
- 弱密码告警（如 `123456` / `admin` / `password`）
- 未使用资源告警
- 多个 resource 共享同一 bind_ip 告警
- V2 resource_id 合法性检查

### Profile / strategy 侧
- username.mode 合法性
- username.start 合法性
- password.mode 合法性
- password.length 合法性
- password.value 非空检查
- port.mode 合法性
- port.start 范围检查

## 用法

```bash
python3 scripts/lint_inventory.py inventory/generated-10ip.yaml --profile profiles/huaweicloud-10ip.yaml
```

## 意义

在 build 之前尽量拦住脏配置，避免生成后才发现冲突。
