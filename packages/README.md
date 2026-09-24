# Client libraries

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Software libraries for applications built on VBOT EDU robots.

Use the [Aorta Python SDK](aorta/python/README.md) or [Aorta C++ SDK](aorta/cpp/README.md).
Its package, native runtime, and installable artifacts are distributed as
vbot-lab release assets (first release `edu-sdk-*`).
A C++ SDK is provided with the release; Rust is not available yet.
Keep Aorta's actual package names, imports, and API contracts.

Use the [Aorta package guide](aorta/README.md), [capability catalog](../catalog/README.md),
[interface reference](../docs/interfaces/README.md), and [Schema](../schemas/README.md)
to select compatible interfaces. Do not infer support from a library name alone.
Check the [compatibility matrix](../release/compatibility.md) before choosing a version.

[Recipes](../recipes/README.md) provide Python and C++ implementations with Bazel
build, run, and test entry points.
