# Preflight Check V1

## 目标

在正式安装前，先检查目标环境是否适合部署，尽量提前发现：
- xray 二进制不存在
- service / config 路径已存在
- 默认 `xray` 服务可能冲突
- 目标端口已被占用
- 当前更适合旁挂测试

## 脚本

- `scripts/preflight_check.py`

## 示例

### 检查默认生成目录
```bash
python3 scripts/preflight_check.py --generated-dir generated-build-10ip
```

### 用测试 service 名检查
```bash
python3 scripts/preflight_check.py --generated-dir generated-build-10ip --service-name xray-test
```

## 输出

输出为 JSON，包含：
- `issues`：硬错误，存在时建议停止安装
- `warnings`：风险提示
- `suggestions`：建议动作
- `bind_checks`：逐条监听探测结果
- `status`：`ok` / `fail`

## V2 改进

- 区分 `ip_not_local` 和 `port_in_use`
- 支持 `--static-only`
- 当 bundle 不是在目标机本地检查时，能提示“建议到目标机执行预检”
