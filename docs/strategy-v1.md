# 策略层 V1

## 目标

把下面这些从“写死”变成“可配置”：
- 用户名生成规则
- 密码生成规则
- 端口生成规则

## 当前支持（profile.strategy）

### username
```yaml
username:
  mode: prefix_counter
  prefix: vip
  start: 1
```

### password
```yaml
password:
  mode: fixed
  value: 123456
```

### port
```yaml
port:
  mode: incremental
  start: 19001
```

## 当前实现范围

当前在 `convert_ip_origin.py` 支持：
- prefix_counter 用户名
- fixed 密码
- random 密码
- incremental 端口

后续可扩展：
- 自定义用户名模板
- 跳号/端口池
- 账号标签独立策略
