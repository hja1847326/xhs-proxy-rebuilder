# 输出风格 V1

## 目标

统一 build / release / preflight / install 这些入口的阶段感和结果感，减少像调试日志的碎片输出。

## 当前约定

### build.py
- `[BUILD:START]`
- `[BUILD:CONVERT]`
- `[BUILD:LINT]`
- `[BUILD:GENERATE]`
- `[BUILD:OK]`

### release.py
- `[RELEASE:START]`
- `[RELEASE:BUILD]`
- `[RELEASE:PACKAGE]`
- `[RELEASE:OK]`

### 子命令执行
- `[RUN:<label>] ...`

## 意义

让整套工具链输出更像一个产品的阶段流，而不是一堆松散脚本日志。
