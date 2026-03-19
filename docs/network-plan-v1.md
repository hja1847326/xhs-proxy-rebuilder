# Runtime Network Plan V1

## 目标

让安装器在远端安装时，不只是复制 xray 配置，还尽量把华为云 `4+N` 资源模型对应的运行态网络补起来。

## 当前自动处理范围

### 自动处理
- VIP (`kind=vip`)：默认补挂到主网卡 `eth0`
- 固定辅助弹性网卡 (`kind=secondary_nic_fixed`)：默认视为已存在于 `eth1`，并自动补策略路由
- `rp_filter`：对 `all` 和 `eth1` 调整为宽松模式 (`2`)
- 源地址策略路由：对固定辅助弹性网卡自动增加 `from <bind_ip> table 100`
- table 100 默认路由：默认走 `192.168.0.1 dev eth1`

### 自动处理（条件式）
- txt 扩展网卡 (`kind=secondary_nic`)：若 `resource-plan.json` 中带 `source_mac`，且系统现有网卡 MAC 命中，则自动挂到对应设备
- 如果系统里找不到对应 MAC，仍输出 `manual_needed ...`

### 仍需人工确认的场景
- 云侧控制台已创建扩展网卡，但系统里尚未热插/枚举到对应设备
- 同一 MAC/设备映射关系异常，或网卡尚未出现在 `ip link show`

## 安装器接入

`install.sh` 默认会读取：
- `generated-build/resource-plan.json`

默认行为：
- `APPLY_NETWORK_PLAN=1`

关闭：
```bash
APPLY_NETWORK_PLAN=0 bash scripts/install.sh generated-build
```

## 已知边界

- 当前 V1 更偏向“运行时补齐固定 4 路”
- `4+N` 中的 `N`（txt 扩展网卡）还需要后续补 MAC→设备 的自动映射策略
- 华为云控制台资源存在，不代表系统里已经热插/枚举到对应设备
