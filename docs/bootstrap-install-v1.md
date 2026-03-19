# Bootstrap / 全局安装 V1

## 目标

把项目内命令壳 `./xhs-proxy` 推进成系统级命令 `xhs-proxy`。

## 脚本

- `scripts/bootstrap_install.sh`

## 默认安装位置

- 可执行命令：`/usr/local/bin/xhs-proxy`
- 运行库目录：`/usr/local/lib/xhs-proxy`

## 支持的环境变量

- `PREFIX`：整体前缀（默认 `/usr/local`）
- `LIB_DIR`：库目录
- `BIN_DIR`：命令目录
- `BIN_NAME`：命令名（默认 `xhs-proxy`）

## 示例

### 正式安装
```bash
sudo bash scripts/bootstrap_install.sh
```

### 安装到临时目录做验证
```bash
PREFIX=/tmp/xhs-proxy-test bash scripts/bootstrap_install.sh
/tmp/xhs-proxy-test/bin/xhs-proxy --help
```

## 当前作用

安装后，机器上就可以直接执行：

```bash
xhs-proxy release ...
xhs-proxy preflight ...
xhs-proxy smoke-test
```

## 当前限制

- 还没有做 curl/bash 远程一键安装 URL
- 仍然基于本地项目文件进行 bootstrap
