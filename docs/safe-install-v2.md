# 安装器安全模式 V2

## 目标

让安装器不再默认硬覆盖系统里的正式 `xray.service`，支持旁挂测试和自定义部署目标。

## 新增能力

### 0. 默认接入 preflight
安装前会默认执行 `scripts/preflight_check.py`。

可通过环境变量控制：
- `RUN_PREFLIGHT=0`：跳过预检
- `PREFLIGHT_STATIC_ONLY=1`：只做静态预检

### 1. 自定义 service 名
默认：
- `SERVICE_NAME=xray`

可改为：
- `SERVICE_NAME=xray-test`
- `SERVICE_NAME=xray-vip`

### 2. 自定义配置路径
默认：
- `/etc/xray/${SERVICE_NAME}.json`

### 3. 自定义 service 路径
默认：
- `/etc/systemd/system/${SERVICE_NAME}.service`

### 4. 可关闭 enable / start
通过环境变量：
- `AUTO_ENABLE=0`
- `AUTO_START=0`

## 示例

### 正式安装
```bash
sudo bash scripts/install.sh generated-build
```

### 旁挂测试模式
```bash
sudo SERVICE_NAME=xray-test AUTO_ENABLE=0 bash scripts/install.sh generated-build
sudo systemctl restart xray-test
sudo systemctl status xray-test --no-pager
```

### 自定义 xray 二进制路径
```bash
sudo XRAY_BIN=/opt/xray/xray bash scripts/install.sh generated-build
```

## 适用场景

- 目标机上已有正式 `xray.service`
- 希望旁挂测试，不影响现网
- 同一台机器部署多套不同实验配置
