# 安装器 V1

## 目标

把生成器产出的配置真正部署到目标机器上。

## 当前行为

`install.sh` 会做这些事：

1. 检查是否 root
2. 检查生成结果是否存在
3. 检查 xray 二进制是否存在
4. 备份旧的配置和 service（如果存在）
5. 拷贝新的：
   - `xray-config.json` -> `/etc/xray/config.json`
   - `xray.service` -> `/etc/systemd/system/xray.service`
6. `daemon-reload`
7. `enable xray`
8. `restart xray`
9. 输出状态

## 用法

```bash
sudo bash scripts/install.sh generated-build
```

## 当前限制

- 暂不自动下载 xray，避免黑盒化
- 默认部署到系统正式路径，后续可扩展为旁挂测试实例模式
- 目前假设 service 名为 `xray`
