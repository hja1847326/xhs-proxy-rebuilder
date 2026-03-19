# Build Manifest V1

## 目标

让 `generated-build/` 在未打包之前，也自带来源说明和生成摘要。

## 新增文件

### build-manifest.json
包含：
- 生成时间（UTC）
- inventory 路径
- profile 路径
- 代理数量
- 资源类型摘要
- 前几条账号样本

### BUILD.README.md
包含：
- 生成时间
- inventory / profile 来源
- 代理数量
- 资源类型
- 样本账号摘要

## 意义

这样即使还没执行 `package_release.py`，单看 `generated-build/` 目录本身，也知道：
- 这是哪次 build
- 用了哪个 profile
- 输入 inventory 是谁
- 生成了多少条代理
