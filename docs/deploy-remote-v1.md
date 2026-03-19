# 远端部署 SOP V1

## 目标

把这套工具链收成一条清晰的跨机器流程：

1. 本地生成 release bundle
2. 把 bundle 传到目标服务器
3. 在目标机先跑远端预检
4. 再执行安装
5. 最后做代理验证

---

## 场景 A：从 `ip_origin.txt` 本地出包

```bash
python3 scripts/release.py \
  --profile profiles/huaweicloud-10ip.yaml \
  --ip-origin ./ip_origin.txt \
  --bundle-dir dist/release-bundle-10ip
```

产物目录示例：
- `dist/release-bundle-10ip/`

---

## 场景 B：把 bundle 传到目标机

可用你习惯的方式：
- `scp`
- `rsync`
- SFTP
- 面板上传

例如：

```bash
scp -r dist/release-bundle-10ip root@YOUR_SERVER:/root/release-bundle-10ip
```

---

## 场景 C：目标机执行远端预检

进入 bundle 目录：

```bash
cd /root/release-bundle-10ip
bash remote_preflight.sh .
```

### 旁挂测试模式

```bash
cd /root/release-bundle-10ip
SERVICE_NAME=xray-test bash remote_preflight.sh .
```

### 预检重点观察

- `issues` 是否为空
- `warnings` 里有没有现网冲突
- `suggestions` 是否建议使用 `xray-test`
- `bind_checks` 是否显示 `bind_ok` / `ip_not_local` / `port_in_use`

> 如果是 `ip_not_local`，通常说明你不是在真正拥有这些 IP 的目标机上执行。

---

## 场景 D：目标机安装

### 正式安装

```bash
cd /root/release-bundle-10ip
bash install.sh .
```

如果 bundle 中包含 txt 扩展路，安装器会额外读取：

- `resource-plan.json`
- `netns-expansion-plan.json`

并自动尝试落地：

- 基础 4 路策略路由
- 扩展路 `VLAN + netns + gost`

### 旁挂测试安装

```bash
cd /root/release-bundle-10ip
SERVICE_NAME=xray-test AUTO_ENABLE=0 bash install.sh .
systemctl restart xray-test
systemctl status xray-test --no-pager
```

### 静态预检后安装

如果你已经确定预检只想走静态模式：

```bash
cd /root/release-bundle-10ip
PREFLIGHT_STATIC_ONLY=1 bash install.sh .
```

### 跳过预检（不推荐）

```bash
cd /root/release-bundle-10ip
RUN_PREFLIGHT=0 bash install.sh .
```

---

## 场景 E：远端验证

### 查看代理清单

```bash
cat proxies.txt
```

### 选一条手工验证

```bash
curl --socks5 192.168.0.10:19001 --proxy-user vip1:YOUR_PASS https://ifconfig.me/ip
```

### 用测试脚本批量验证

```bash
python3 test_proxies.py proxies.json --endpoint https://ifconfig.me/ip
```

---

## 推荐标准流程

### 新机器标准部署
1. 本地 `release.py` 出 bundle
2. 把 bundle 传到目标机
3. 目标机执行 `bash remote_preflight.sh .`
4. 如有现网风险，改用 `SERVICE_NAME=xray-test`
5. 执行 `bash install.sh .`
6. 用 `test_proxies.py` 或 curl 验证
7. 再决定是否转正式服务名

---

## 常见分支判断

### 1. 预检报 `xray binary not found`
说明目标机还没装 xray，先补二进制再继续。

### 2. 预检报 `port_in_use`
说明监听端口真冲突了，要么换端口，要么先清理现有占用。

### 3. 预检报 `ip_not_local`
说明这台机子并不拥有对应 bind IP，别硬装。

### 4. 预检发现已有 `xray.service`
优先考虑：

```bash
SERVICE_NAME=xray-test AUTO_ENABLE=0 bash install.sh .
```

先旁挂，别直接顶现网。

### 5. txt 扩展路（4+N 中的 N）
如果你要验证 txt 扩展路，不要沿用“主命名空间旁挂扩展 IP”的旧思路。真实成功机与新机第 5 路验证结果表明：

- 基础 4 路：可按主命名空间 + 策略路由处理
- txt 扩展路：应按 `VLAN + netns + gost` 模型处理

参考：`docs/netns-expansion-v1.md`

---

## 当前限制

1. 远端预检目前以 bundle 内 `proxies.txt` 为输入
2. 当前主要面向华为云这类多 IP / VIP / 辅助网卡场景
3. 最终大规模量产前，仍建议喂更多真实样本继续验证
