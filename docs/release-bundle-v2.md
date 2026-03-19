# Release Bundle V2

## 目标

让打包结果不仅能安装，还能追溯“它是怎么生成的”。

## 新增内容

### bundle-meta.json
记录：
- 打包时间（UTC）
- bundle 目录
- generated 目录
- profile 路径
- inventory 路径
- 已复制文件列表

### BUNDLE.README.md
记录：
- 这个包是什么
- 来源 profile / inventory
- 打包文件列表
- 常用安装命令
- 旁挂测试安装命令

### source-profile.yaml
如果打包时传入 `--profile`，会把 profile 副本打进去。

### source-inventory.yaml
如果打包时传入 `--inventory`，会把 inventory 副本打进去。

## 示例

```bash
python3 scripts/package_release.py \
  --generated-dir generated-build-10ip \
  --bundle-dir dist/release-bundle-10ip \
  --profile profiles/huaweicloud-10ip.yaml \
  --inventory inventory/generated-10ip.yaml
```
