# 输出风格 V3

## 目标

继续统一“结论感”，让主要入口在结束时给出更直白的成功/警告/停止信号。

## 当前约定

### 成功结论
- `[OK] build_complete`
- `[OK] release_complete`
- `[OK] install_complete`
- preflight summary: `[OK] decision=proceed`

### 警告结论
- preflight summary: `[WARN] decision=caution`

### 失败结论
- preflight summary: `[FAIL] decision=stop`

## 意义

让人扫一眼最后几行，就知道：
- 能继续
- 该谨慎
- 还是必须停下
