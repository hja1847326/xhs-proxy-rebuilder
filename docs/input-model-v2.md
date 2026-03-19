# 输入模型 V2 说明

## 为什么升级

V1 直接在 `proxies` 里手填：
- listen_ip
- send_through
- expected_public_ip

这种方式能跑，但不适合扩到 10/20 IP。

V2 把输入拆成两层：

1. `resources.egresses`
   - 表示真实的出口资源
   - 对应华为云里的主 IP / VIP / 辅助网卡

2. `proxies`
   - 表示业务侧实际要使用的代理
   - 通过 `resource_id` 绑定到某个出口资源

## 结构

### resources.egresses
每个出口资源定义：
- `id`: 资源唯一标识
- `bind_ip`: xray `sendThrough` 使用的源地址
- `expected_public_ip`: 预期公网出口 IP
- `kind`: `primary` / `vip` / `secondary_nic`
- `note`: 备注

### proxies
每条代理定义：
- `name`
- `resource_id`
- `listen_ip`
- `port`
- `username`
- `password`
- `account_label`

## 这样做的好处

1. 资源和代理分离，扩容不乱
2. 一眼看出哪个代理走哪个出口资源
3. 后面更容易从华为云原始清单自动生成资源层
4. 适合做账号与网络的长期映射管理
