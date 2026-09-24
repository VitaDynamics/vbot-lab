# 四足 EDU 模型资源

<p align="center"><a href="README.md">English</a> | 中文</p>

模型：**VbotBaboEDU**。设备类型：`foot_quadruped`。

当前目录仅预留模型位置，**未附带 URDF、网格或纹理文件**。
[model.json](model.json) 的 `availability` 为 `not_bundled`，`urdf` 为 `null`，
当前仓库没有可从此处加载的模型。

可打开[在线模型](https://vbot-viewer.vitarobot.cc/?model=VbotBaboEDU)，
按 [Viewer 指南](../../../docs/guides/vbot-viewer.zh-CN.md)查看结构。
网站中的模型与本地资源目录是独立的。

## 资源布局

- `urdf/`：预留 URDF 描述及其入口文件的位置。
- `meshes/`：预留上述描述引用的网格位置。
- `textures/`：可选，仅在模型文件存在纹理依赖时创建。
- `model.json`：具体模型标识、设备类型、公开 Viewer 地址与本地可用状态。

URDF 和网格占位目录不包含示例或备用机器人。目前没有可运行的模型目标，
`BUILD.bazel` 仅为仓库检查提供元数据与文档。
具体硬件修订、坐标约定、资源版本与许可条款，待模型包提供后再说明，不预先假定。

设备开发见[四足 EDU 指南](../../../docs/robots/foot_quadruped/README.zh-CN.md)。
模型问题与建议可按[社区与支持](../../../docs/community/README.zh-CN.md)反馈。
