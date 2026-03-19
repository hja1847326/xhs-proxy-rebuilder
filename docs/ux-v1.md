# UX 收口 V1

## 目标

统一 preflight / install / remote bundle 这些入口的输出体验，减少“给一坨 JSON 自己啃”的情况。

## 新增脚本

- `scripts/render_preflight_summary.py`

作用：
- 读取 preflight JSON
- 输出更人话的摘要
- 给出简单决策：`stop` / `caution` / `proceed`

## 当前接入点

### install.sh
安装器在执行 preflight 后，会同时输出：
- 原始 JSON
- 人类可读摘要

### release bundle
打包时会带上：
- `render_preflight_summary.py`

这样目标机也能直接把远端预检结果转成摘要。

## 后续可继续统一

- remote_preflight.sh 直接内联摘要
- release.py 输出统一收口
- build / validator / preflight 使用类似的状态头
