# CLI V1

## 目标

把当前散落的脚本入口统一收成一个总命令壳：`xhs-proxy`。

## 当前文件

- `xhs-proxy`（项目根目录命令壳）
- `scripts/xhs_proxy_cli.py`（CLI 分发器）

## 当前支持的子命令

```bash
./xhs-proxy build ...
./xhs-proxy release ...
./xhs-proxy install ...
./xhs-proxy preflight ...
./xhs-proxy smoke-test
```

## 示例

### 跑 smoke tests
```bash
./xhs-proxy smoke-test
```

### 跑静态预检
```bash
./xhs-proxy preflight -- --generated-dir generated-build-10ip --static-only
```

### 一把出包
```bash
./xhs-proxy release -- --profile profiles/huaweicloud-10ip.yaml --ip-origin ./ip_origin.txt
```

## 当前限制

- 目前还是项目内命令壳（`./xhs-proxy`）
- 还没做成系统级全局命令
- 还没做 curl/bash 一键安装 bootstrap

## 下一步

- 做 bootstrap 安装脚本
- 支持把 `xhs-proxy` 安装到 `/usr/local/bin/`
- 再往后做真正的一条命令安装
