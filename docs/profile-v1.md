# Profile 配置层 V1

## 目标

让项目不再围着某一台机器写死，而是通过 profile 抽出可复用默认值。

## 当前内容

`profiles/huaweicloud-default.yaml`

包含：
- `primary_ip`
- `vip_ips`
- `start_port`
- `default_password`
- `output_dir`
- `inventory_output`

## 作用

以后换机器时，不需要改脚本逻辑，只需要：
- 换 `ip_origin`
- 换/扩 profile
- 重新 build

## 下一步

- build.py 读取 profile 默认值
- 支持自定义 profile
- 支持更多命名和密码生成策略
