# 发布配置

<p align="center"><a href="release.md">English</a> | 中文</p>

[release.json](release.json) 记录一个 VBOT Lab 源码快照的组件组合。
它是本地、机器可读的配套配置，不是发布公告或安装程序，各组件保留独立版本号。

配置记录所选应用、SDK、Schema 与开发镜像引用，以及计划使用的源码分支和 tag；
这不会创建 Git 引用，也不表示发布了新版本。镜像 digest 尚未记录。

## 字段说明

| 字段 | 含义与填写范围 |
| --- | --- |
| `format_version` | 整数 `1`；拒绝未知字段和重复 JSON 键 |
| `workspace.branch` | 正式版本使用 `main`，迭代版本使用 `pre_release/V1.6.0.X` 等长期分支；`X` 保留为字母，不替换为迭代号 |
| `workspace.tag` | 计划使用的源码 tag，准备阶段可为 `null`；迭代 tag 必须与分支版本族一致，例如 `pre_release/V1.6.0.X` 对应 `V1.6.0.10`。机器人应用和 SDK 版本仍分别管理 |
| `robots` | `catalog/robots/` 中当前已开放的设备类型；分别记录准确的 `application_version`，不是最低版本 |
| `sdk.repository`、`sdk.release_tag` | 公开 GitHub 下载仓库（`owner/name`）和 SDK Release tag；复用 SDK 时保持其原 tag |
| `sdk.aorta_version` | 与 Python、C++ SDK 配套的 Aorta 版本 |
| `sdk.python` | 最低 Python 版本（`major.minor`）、四个 wheel 包的准确版本和可下载的 wheel 平台标签 |
| `sdk.cpp` | 准确的 SDK 版本、正整数 ABI、发行环境标识和可下载架构；ABI 与 Bazel 的原生库导入保持一致 |
| `sdk.assets` | 附件清单：准确文件名与 64 位小写 SHA-256，包含校验文件、manifest 和许可证附件；不记录凭据或带签名的下载 URL |
| `schema` | 来自生成文件 `schemas/MANIFEST.json` 的 Schema 版本、pack 修订、归档名／校验值及 ROS 2 bridge 配套版本；pack 修订与 Schema 版本可不同 |
| `development.bazel_version` | `.bazelversion` 中的准确值 |
| `development.image` | Compose 默认镜像的带 tag 引用及 `sha256:<64 位小写十六进制>` digest；`null` 表示尚未记录 digest |

包版本使用三段数字，可追加 `-v4` 等修订后缀；应用版本使用 `V<major>.<minor>.<patch>`，可追加 `-10` 等数字构建后缀。
兼容关系未知时，不要复制其他组件的版本号来填充。

指南、接口文档、Recipes、Blueprints、Skills、工具、索引、硬件／模型资源和构建配置
均属于源码快照，不必为每个目录单独定义发布版本。下载的 SDK 二进制
记录自己的 Release 引用与校验值。

## 源码分支与 tag

VBOT Lab 的 `main` 保存正式版本。迭代更新在选定版本族的
`pre_release/V<major>.<minor>.<patch>.X` 分支中准备。
每个版本族使用各自的分支；`pre_release/V1.6.0.X` 仅对应 `V1.6.0` 版本族。
迭代更新允许直接提交和推送，不要求 PR。
例如，机器人应用 `V1.6.0-10` 可配套源码 tag `V1.6.0.10`，对应
`pre_release/V1.6.0.X`；准确的 SDK／Schema 配套另行记录。

在检查通过的源码提交上创建迭代 tag。仅打 tag 不会将迭代版本提升到 `main`，
也不会创建 GitHub Release。后续迭代继续在选定分支上进行，只有明确要求正式发布时，
才创建提升 PR。已有 tag 对应不可变的源码快照；在已打 tag 的快照之后继续修改时，
新 tag 选定前将 `workspace.tag` 保留为 `null`，不复用或移动已有 tag。
评审和正式发布步骤见[协作流程](../.github/WORKFLOWS.zh-CN.md)。

配置不替代[能力元数据](README.zh-CN.md)、设备配置、生成的 Schema 元数据或 SDK
安装说明。检查工具比较这些来源，报告不一致的组合，不会自动改写它们。

## 检查配套关系

在仓库根目录使用 Python 3.10+：

```bash
python3 tools/check_release.py
python3 tests/test_release.py
```

工具仅使用标准库和本地文件，不访问 GitHub、Docker 或设备，不安装依赖、创建 tag
或发布 Release。输出为 JSON：退出码 `0` 表示本地配套一致（仍可能有 `pending` 字段）；
`1` 表示要求严格完整检查但仍有未填写字段；`2` 表示输入错误或配套不一致。
命令行参数错误也返回 `2`，argparse 信息输出至 stderr。

要求填齐源码 tag 和镜像 digest：

```bash
python3 tools/check_release.py --require-complete
```

完整检查只确认语法和记录的配套关系，不证明 tag 已存在、
下载可见性、镜像身份或设备兼容性。镜像 digest 或源码 tag 未填齐时，会按预期无法通过严格检查。

按 [SDK 指南](../packages/aorta/python/README.zh-CN.md)下载 SDK 附件后，
可选地比较发布 manifest 并计算本地附件校验值：

```bash
SDK_RELEASE_TAG=$(python3 -c 'import json; print(json.load(open("catalog/release.json"))["sdk"]["release_tag"])')
python3 tools/check_release.py \
  --sdk-manifest "artifacts/${SDK_RELEASE_TAG}/EDU_SDK_MANIFEST.json" \
  --sdk-assets-dir "artifacts/${SDK_RELEASE_TAG}"
```

目录必须包含 `sdk.assets` 列出的**全部**附件；单个平台的 SDK 安装文件不等于完整清单。
忽略额外无关文件，拒绝缺失、内容变化或软链接附件。仅比较 SDK manifest 是检查元数据，
不是核验二进制内容。

## 更新时保持一致

| 变化组件 | 联动检查内容 |
| --- | --- |
| 源码快照／设备支持 | 源码分支／tag、设备配置、`docs/compatibility.md`、`AGENTS.md`、能力范围与 changelog；不要移动已有 tag |
| SDK／原生 ABI | 公开 Release 附件清单与校验值、`catalog/capabilities.json`、Python／C++ 安装指南、`recipes/common.py` 版本约束及 `packages/aorta/cpp/repositories.bzl` 原生库导入 |
| Schema／路由 | 生成的 `schemas/` 和 `schemas/MANIFEST.json`、SDK 生成绑定、公开接口文档与能力引用；重新生成，不手工修改生成文件 |
| 指南／Recipes／Skills／工具 | 双语文档、索引与任务导航、配置／部署说明和测试；变更后的在线示例按[贡献规范](../CONTRIBUTING.zh-CN.md)先完成设备检查再公开 |
| 开发环境 | Compose 镜像引用与 digest、`.devcontainer/`、`.bazelversion`、Bazel module／lockfile 与工具前置要求 |
| 硬件／模型 | 资源 manifest、设备类型适用范围、文档和授权声明 |
| 测试预期 | 离线测试及其中与版本有关的预期；检查不会自动迁移示例或依赖 |

只更新发生变化的组件；仅更新文档的源码版本可以复用既有 SDK Release。
配置可供本地工具读取，目前没有配置自动发布。
