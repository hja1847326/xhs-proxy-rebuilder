# Roadmap / Checklist V1

## 项目目标

做一套 **可复制、可迁移、可在多台华为云机器复用** 的多 SK5 生成 / 安装 / 打包方案，替代原黑盒激活脚本，但不复刻其激活逻辑。

---

## 一、已完成（核心骨架）

### 输入与建模
- [x] 支持 `ip_origin.txt` 转 inventory
- [x] 默认按 `IP + VLAN + MAC` 解析
- [x] 保留 `IP + MAC + VLAN` 兼容兜底
- [x] 支持 inventory V2（resources.egresses + proxies）
- [x] 引入 profile 配置层

### 策略层
- [x] 用户名策略：`prefix_counter`
- [x] 密码策略：`fixed`
- [x] 密码策略：`random`
- [x] 端口策略：`incremental`
- [x] 提供 `huaweicloud-default / 10ip / 20ip` profile 样例

### 校验层
- [x] inventory lint
- [x] profile / strategy lint
- [x] 重复端口检测
- [x] 重复用户名检测
- [x] 重复 listen endpoint 检测
- [x] 弱密码告警
- [x] 未使用资源告警
- [x] smoke tests / 错误样例 V1

### 生成层
- [x] 生成 `xray-config.json`
- [x] 生成 `xray.service`
- [x] 导出 `proxies.txt / csv / json`
- [x] 生成 `INSTALL.md`
- [x] 生成 `build-manifest.json`
- [x] 生成 `BUILD.README.md`

### 安装层
- [x] 安装器 V1
- [x] 安装器安全模式 V2
- [x] 支持自定义 `SERVICE_NAME`
- [x] 支持自定义 `XRAY_BIN`
- [x] 支持 `AUTO_ENABLE=0`
- [x] 支持 `AUTO_START=0`

### 打包与发布
- [x] `package_release.py`
- [x] Release Bundle V2
- [x] bundle 元数据 `bundle-meta.json`
- [x] `BUNDLE.README.md`
- [x] profile / inventory 副本随包携带
- [x] `release.py` 总入口 V1

### 文档
- [x] design / input-model / converter / lint / build 文档
- [x] profile / strategy / usage-flow 文档
- [x] safe-install / release-bundle / manifest / validator / smoke-tests 文档

---

## 二、已验证（方向成立）

- [x] 在新测试机上透明安装官方 Xray 成功
- [x] 最小 SOCKS5 实例可启动、监听、认证
- [x] 代理请求经 `ifconfig.me` 验证可返回公网出口 IP
- [x] 证明不用原激活脚本也能跑通核心链路

> 注：单机验证仅用于证明路线成立，不是最终目标。

---

## 三、当前还差（走向真正交付版）

### 资源侧
- [ ] 更多真实华为云资源样本（特别是 `4+N` 模型下的多行 `ip_origin`）
- [x] 已确认 txt 扩展网卡的正确运行态模型：`VLAN + netns + gost`
- [ ] 多 VIP / 固定辅助网卡 + 多扩展网卡的真实 inventory 样本
- [ ] 不同机器规格下的 profile 调优建议

### 生成 / 策略侧
- [ ] 更灵活的用户名模板
- [ ] 账号标签独立策略
- [ ] 端口池 / 跳号策略
- [ ] 生成后端口冲突的跨批次检查

### 安装 / 运维侧
- [ ] 更完整的旁挂测试指引
- [x] 目标机环境探测（已有 xray / 端口占用 / systemd 冲突）
- [x] 扩展路 `VLAN + netns + gost` 运行态自动化初版接入安装器
- [ ] 更明确的回滚流程
- [ ] 可选的离线包安装模式

### 验证侧
- [ ] 更标准化的代理验证报告
- [ ] 对多个验证站点的结果汇总
- [ ] 生成后自动抽样测试

### 交付侧
- [ ] 最终对外教程 / 实战部署手册
- [ ] 常见报错排查手册
- [ ] 新机器从 0 到可用的标准 SOP

---

## 四、当前建议优先级

### P1（最值钱）
- [x] 做目标机环境探测 / preflight check
- [ ] 做更完整的回滚与旁挂测试流程
- [ ] 补更多真实资源样本验证通用性

参考：`docs/validation-matrix-v1.md`

### P2（增强可复制性）
- [ ] 做更灵活的策略模板
- [ ] 做更标准化的验证报告
- [ ] 完成部署手册 / FAQ

### P3（锦上添花）
- [ ] 更花的命名模板
- [ ] 更多 profile 预设
- [ ] 更多输出格式

---

## 五、当前一句话状态

> 这项目已经从“试着在一台机子上跑通”进化到“具备输入、策略、校验、生成、安装、打包、发布、文档、测试骨架的可复制工具链”，但距离真正交付版还差 **环境探测、回滚/SOP、更多真实样本验证** 这三块。
