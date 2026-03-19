# 远端预检 V1

## 目标

让 release bundle 到达目标服务器后，可以在目标机本地先做一轮预检，再决定是否安装。

## 脚本

- `scripts/remote_preflight.sh`
- 打包后会出现在 bundle 里：`remote_preflight.sh`

## 用法

在目标机的 bundle 目录中执行：

```bash
bash remote_preflight.sh .
```

### 旁挂测试
```bash
SERVICE_NAME=xray-test bash remote_preflight.sh .
```

## 检查内容

- `xray` 二进制是否存在
- `systemctl` 是否存在
- 目标 config / service 文件是否已存在
- 目标 service 是否已在运行
- 其他 xray-like services 是否存在
- `proxies.txt` 中监听 IP 是否属于当前机器
- 目标端口是否已被占用

## 输出

默认同时输出：
- 原始 JSON
- 人类可读摘要（如果 bundle 中存在 `render_preflight_summary.py`）

JSON 包含：
- `issues`
- `warnings`
- `suggestions`
- `bind_checks`
- `status`

## 控制项

- `RENDER_SUMMARY=0`：只输出 JSON，不渲染摘要
- `SUMMARY_RENDERER=/path/to/render_preflight_summary.py`：指定摘要渲染器路径
