# xhs-proxy-rebuilder

面向华为云 ECS 的“小红书矩阵一账号一网络”代理重构项目。

## 目标

重做一套不依赖激活码的多出口 SOCKS5 方案，替代旧的黑盒安装器。

核心目标：
- 一个账号尽量固定一条代理
- 一条代理固定一个出口身份
- 配置透明，可维护，可迁移
- 支持验证每个代理的真实出口 IP

## 当前范围（V1）

先做华为云专用版，围绕下列资源模型：
- 1 台华为云 ECS
- 固定基础 4 路：主网卡 + 2 个 VIP + 1 个固定辅助弹性网卡
- txt 扩展 N 路：每行 `IP VLAN MAC`（或兼容 `IP MAC VLAN`）代表 1 个额外扩展出口
- 总代理数模型：`4 + N`
- 多个 EIP
- 单机多出口 SOCKS5
- 基础 4 路以 Xray 为主，txt 扩展路按 `VLAN + netns + gost` 模型落地

## 计划分期

### V1 原型版
- 读取华为云资源清单
- 生成 xray 配置
- 生成 systemd 服务文件
- 导出代理列表
- 本机测试代理认证与出口 IP

### V2 扩展版
- 更完整的华为云资源校验
- 自动生成账号密码
- 10/20 IP 模式
- 更完善的运维脚本
- Profile / 策略层
- 标准使用流程

## 当前主入口

### 从 `ip_origin.txt` 构建
```bash
python3 scripts/build.py --profile profiles/huaweicloud-default.yaml --ip-origin ./ip_origin.txt
```

### 打包发布
```bash
python3 scripts/package_release.py --generated-dir generated-build
```

### 目标机安装
```bash
sudo bash scripts/install.sh generated-build
```

默认会同时尝试：
- 基础 4 路运行态补齐（`resource-plan.json`）
- txt 扩展路 `VLAN + netns + gost` 落地（`netns-expansion-plan.json`）

如果目标机没有 `gost`，可额外提供：
```bash
sudo GOST_SOURCE=/path/to/gost bash scripts/install.sh generated-build
```

详细流程见：`docs/usage-flow-v1.md`

## 当前状态

- 项目状态 / 已完成与待完成：`docs/roadmap-v1.md`
- 发布总入口：`scripts/release.py`
- 远端部署 SOP：`docs/deploy-remote-v1.md`
- 验证矩阵：`docs/validation-matrix-v1.md`
- CLI 入口：`docs/cli-v1.md`
- 全局安装：`docs/bootstrap-install-v1.md`
- 远程安装：`docs/remote-install-v2.md`
- 扩展路模型：`docs/netns-expansion-v1.md`
- 扩展路验证：`docs/netns-validation-v1.md`
- 安装后健康检查：`docs/healthcheck-install-v1.md`
- 第 5 路复盘：`docs/fifth-route-retrospective-v1.md`

## 项目结构

- `inventory/` 输入清单
- `generated/` 生成结果
- `scripts/` 管理脚本
- `docs/` 设计与测试文档

## 设计原则

1. 不依赖黑盒安装器
2. 不耦合激活码
3. 优先纯 xray 架构
4. 所有代理关系可导出、可验证
5. 先做 4 代理原型，再扩到 10/20
