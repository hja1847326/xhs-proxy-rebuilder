# 输出风格 V2

## 目标

继续压缩底层脚本噪音，让上层入口（build/release）主导输出节奏。

## 新增 quiet 模式

以下脚本已支持 `--quiet`：
- `convert_ip_origin.py`
- `lint_inventory.py`
- `generate.py`
- `package_release.py`

## 当前接入

### build.py
默认以 `--quiet` 调用：
- convert
- lint
- generate

### release.py
默认以 `--quiet` 调用：
- package_release

## 效果

主流程更突出：
- 阶段头
- 关键路径
- 最终结果

底层细碎摘要默认收起来，除非：
- 你直接单独运行底层脚本
- lint 发生错误（即使 quiet 也会吐错误）
