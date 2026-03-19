# ip_origin 转换器 V1

## 目标

把原教程里最烦的 `ip_origin.txt` 转成我们自己的 V2 inventory。

## 输入格式

每行三列：

```text
IP MAC VLAN
```

例如：

```text
192.168.1.250 aa:bb:cc:dd:ee:01 4010
```

## 转换结果

会自动生成：
- `resources.egresses`
  - `main`
  - `vip1`
  - `vip2`
  - `nic1..nicN`
- `proxies`
  - `proxy01..proxyNN`
  - 账号默认命名为 `vip1..vipN`
  - 端口从 `19001` 开始递增

## 默认规则

- 主 IP：`192.168.0.10`
- VIP：`192.168.0.11`、`192.168.0.12`
- 默认密码：`123456`

## 示例命令

```bash
python3 scripts/convert_ip_origin.py inventory/ip_origin.sample.txt
```

## 可调参数

- `--primary-ip`
- `--vip`
- `--start-port`
- `--default-password`
- `--output`
