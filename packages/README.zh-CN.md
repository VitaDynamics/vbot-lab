# 客户端开发库

<p align="center"><a href="README.md">English</a> | 中文</p>

为 VBOT EDU 机器人应用提供软件开发库。

可选择 [Aorta Python SDK](aorta/python/README.zh-CN.md) 或 [Aorta C++ SDK](aorta/cpp/README.zh-CN.md)。
软件包、原生运行库与可安装制品通过 vbot-lab Release 附件分发（首版 `edu-sdk-*`）。
Release 提供 C++ SDK；暂不提供 Rust。
保留 Aorta 实际包名、导入路径和 API 契约。

通过 [Aorta 包指南](aorta/README.zh-CN.md)、[能力索引](../catalog/README.zh-CN.md)、
[接口参考](../docs/interfaces/README.zh-CN.md)和 [Schema](../schemas/README.zh-CN.md)选择兼容接口。
不能仅凭库名推断支持范围；选择版本前核对[兼容矩阵](../docs/compatibility.zh-CN.md)。

[Recipes](../recipes/README.zh-CN.md)提供聚焦单项任务的 Python 与 C++ 实现，
包含 Bazel 构建、运行及测试入口。
