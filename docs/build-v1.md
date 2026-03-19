# 统一入口 build.py

## 目标

把现在已有的三个核心步骤串起来：

1. `convert_ip_origin.py`
2. `lint_inventory.py`
3. `generate.py`

这样后面就可以逐步收敛成一键化流程。

## 两种用法

### 用现成 inventory

```bash
python3 scripts/build.py --inventory inventory/huaweicloud-v2-sample.yaml --output-dir generated-build
```

### 用 ip_origin 直接构建

```bash
python3 scripts/build.py \
  --ip-origin /path/to/ip_origin.txt \
  --output-dir generated-build
```

## 可调参数

- `--primary-ip`
- `--vip`（可重复）
- `--start-port`
- `--default-password`
- `--inventory-output`

## 当前定位

这是“统一入口 V1”，先解决：
- 输入转换
- 校验
- 生成

后续再往一键安装继续收。
