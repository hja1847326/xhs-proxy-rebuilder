# Inventory 校验器 V1

## 目标

在真正生成配置、部署到服务器之前，先把明显的脏配置挡住。

## 当前检查项

### 错误（阻断）
- 缺少 `proxies`
- 资源 ID 重复
- 资源 bind_ip 缺失或非法
- 代理名重复
- 端口非法或重复
- 缺少 username / password
- V2 中引用不存在的 `resource_id`
- V1 中缺少 `send_through`

### 警告（不阻断）
- 资源 bind_ip 重复
- username 重复
- `listen_ip` 与资源 `bind_ip` 不一致
- `account_label` 缺失
- 代理数量偏少

## 示例

```bash
python3 scripts/lint_inventory.py inventory/huaweicloud-v2-sample.yaml
python3 scripts/lint_inventory.py inventory/from-user-ip-origin.yaml
```
