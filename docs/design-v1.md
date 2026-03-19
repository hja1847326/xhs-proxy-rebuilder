# 华为云专用版替代程序设计 V1

## 背景

现有旧方案依赖黑盒二进制安装器和激活码，真实落地表现为：
- 多 IP / 多网卡 / VIP
- xray + gost 混合
- 配置和运维不透明
- 进程管理不够整洁

V1 目标是先做一个可读、可控、可验证的替代程序原型。

## V1 范围

- 聚焦华为云现有资源模型
- 先实现 4 代理原型版
- 使用 xray 作为唯一代理内核
- 由结构化 inventory 生成配置
- 支持导出代理清单
- 支持验证真实出口 IP

## 输入

`inventory/huaweicloud-sample.yaml`

每条代理定义：
- `name`
- `listen_ip`
- `port`
- `username`（当前先按 `vip1`、`vip2`、`vip3` 风格）
- `password`
- `send_through`
- `expected_public_ip`
- `account_label`

## 输出

### 1. xray 配置
路径建议：
- `/etc/xray/config.json`
或
- `/etc/xray/generated-config.json`

### 2. systemd 服务文件
路径建议：
- `/etc/systemd/system/xray.service`

### 3. 代理导出列表
便于业务侧使用：
- `generated/proxies.txt`
- `generated/proxies.csv`
- `generated/proxies.json`

## 运行模型

### 入站
每条代理生成一个 socks 入站：
- 监听指定 IP
- 使用独立端口
- 启用用户名密码认证
- 启用 UDP

### 出站
每条代理生成一个 freedom 出站：
- `sendThrough` 指向指定源地址

### 路由
按入站 tag 将请求路由到对应出站。

## 验证

每条代理至少验证：
1. 端口监听存在
2. 用户名密码认证成功
3. 访问 ipify / ifconfig.me 时出口 IP 与 `expected_public_ip` 一致（若配置了预期值）

## 后续扩展

- V2: 华为云资源清单自动转换器（从原始 IP/MAC/VLAN 清单生成 inventory）
- V3: 10/20 代理批量生成
- V4: 安装、升级、回滚脚本

## 运行态模型修正（新增结论）

基础 4 路仍可按主命名空间 + 策略路由处理，但 txt 扩展路（`4+N` 中的 `N`）已通过真实成功机只读分析与新机第 5 路运行态验证确认：

- 正确模型为：`VLAN 子接口 + netns + gost`
- 错误模型为：在主命名空间直接旁挂扩展 IP

也就是说，扩展路并不是基础 4 路的简单平移，而是应被视为独立命名空间内的出口单元。
