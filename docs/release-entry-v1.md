# Release 总入口 V1

## 目标

把原本分散的：
- convert
- lint
- generate
- manifest
- package

收敛成一条总入口命令。

## 脚本

- `scripts/release.py`

## 标准用法

### 从 ip_origin 一把生成并打包
```bash
python3 scripts/release.py \
  --profile profiles/huaweicloud-10ip.yaml \
  --ip-origin ./ip_origin.txt \
  --bundle-dir dist/release-bundle-10ip
```

### 从现成 inventory 一把生成并打包
```bash
python3 scripts/release.py \
  --profile profiles/huaweicloud-default.yaml \
  --inventory inventory/generated-10ip.yaml \
  --bundle-dir dist/release-bundle-existing
```

## 做了什么

1. 调 `build.py`
2. 自动定位 generated output
3. 调 `package_release.py`
4. 生成 release bundle

## 意义

以后更像真正的交付命令，而不是一堆手工拼装步骤。
