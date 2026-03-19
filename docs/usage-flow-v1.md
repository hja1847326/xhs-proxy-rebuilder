# 使用流程 V1

## 目标

把当前工具链收敛成一套清晰、可复用的标准操作流程。

---

## 场景 1：从 `ip_origin.txt` 直接构建

适合华为云新机器，手里已经有 `ip_origin.txt`。

### 默认 profile
```bash
python3 scripts/build.py \
  --profile profiles/huaweicloud-default.yaml \
  --ip-origin ./ip_origin.txt
```

### 10IP profile
```bash
python3 scripts/build.py \
  --profile profiles/huaweicloud-10ip.yaml \
  --ip-origin ./ip_origin.txt
```

### 20IP profile
```bash
python3 scripts/build.py \
  --profile profiles/huaweicloud-20ip.yaml \
  --ip-origin ./ip_origin.txt
```

### 产物
构建完成后会得到：
- inventory YAML
- xray-config.json
- xray.service
- proxies.txt / csv / json

---

## 场景 2：使用现成 inventory 直接生成

适合已经整理好资源映射关系时。

```bash
python3 scripts/build.py \
  --inventory inventory/huaweicloud-v2-sample.yaml \
  --output-dir generated-build
```

---

## 场景 3：打包成发布目录

```bash
python3 scripts/package_release.py \
  --generated-dir generated-build \
  --bundle-dir dist/release-bundle
```

打包后会有：
- xray-config.json
- xray.service
- proxies.txt / csv / json
- install.sh
- test_proxies.py
- INSTALL.generated.md

---

## 场景 4：目标机安装

前提：目标机已具备 `xray` 二进制。

```bash
sudo bash scripts/install.sh generated-build
```

或者对发布包目录执行：

```bash
sudo bash dist/release-bundle/install.sh dist/release-bundle
```

---

## 场景 5：代理验证

### 直接查看代理清单
```bash
cat generated-build/proxies.txt
```

### 用测试脚本验证
```bash
python3 scripts/test_proxies.py generated-build/proxies.json --endpoint https://ifconfig.me/ip
```

### 手工验证单条代理
```bash
curl --socks5 192.168.0.10:19001 --proxy-user vip1:123456 https://ifconfig.me/ip
```

---

## 推荐工作流

### 新机器标准流程
1. 拿到 `ip_origin.txt`
2. 选择一个 profile
3. 执行 `build.py`
4. 检查 `proxies.txt`
5. 打包（可选）
6. 在目标机安装 xray
7. 执行 `install.sh`
8. 用 `test_proxies.py` 或 curl 验证

---

## 现阶段已知限制

1. 当前安装器默认正式路径 `/etc/xray/config.json`
2. 当前主要面向华为云结构
3. `ip_origin` 默认按 `IP + VLAN + MAC` 解析
4. 随机密码已支持，但更复杂的命名模板还没做
