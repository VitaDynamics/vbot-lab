# 离线构建示例

<p align="center"><a href="offline-build.md">English</a> | 中文</p>

使用 Bazel 7.6.1 和配套依赖包，无需从注册表下载构建规则即可构建。
依赖包包含 Python／C++ Recipes 所需的公开规则、注册表元数据和上游许可证，
不包含 Aorta SDK、编译器、Python 解释器或 FFmpeg。

## 准备构建环境

从开发环境提供方取得配套依赖包，或按下文在联网机器上生成。
当前 SDK 预发布版本尚未附带预构建依赖包；准备工具不会自动发布它，
也不要假设现有开发镜像已经包含它。

断网前准备好以下内容：

- Bazel 7.6.1、本机架构的 C++17 编译器及配套 Linux 系统头文件／库。
- 匹配当前 `MODULE.bazel` 和 `MODULE.bazel.lock` 的构建依赖包。
- 配套的 [C++ SDK 和 Schema 包](../../packages/aorta/cpp/README.zh-CN.md)。
- Python 执行所需的 [SDK wheel](../../packages/aorta/python/README.zh-CN.md)
  和 FlatBuffers wheel，安装到专用 venv。
- 可选图像解码：Python 需要兼容的 `av==16.1.0` 和 `numpy==2.2.6` wheel；C++ 需要 FFmpeg 开发库和运行库。
  Bazel 不会安装这些依赖。

SDK 制品需要先联网从 GitHub Releases 下载。`edu-sdk-2026.9.24` Release 在 SDK wheel
旁附带 `flatbuffers` 25.12.19 wheel；[Python 部署指南](python-deployment.zh-CN.md)
也说明了如何从 PyPI 获取。同时准备所需的可选依赖。下方命令以已备齐、已校验的
wheelhouse 为前提。

把全部 wheel 集中到 wheelhouse 后，再执行不访问包索引的安装：

```bash
python -m pip install --no-index --find-links artifacts/wheelhouse \
  aorta-sdk==2026.9.23 aorta-msgs==2026.9.23 vbot-edu-msgs==2026.9.24 flatbuffers==25.12.19
```

## 使用依赖包构建

校验依赖包后解压到 `artifacts/offline/bazel/`，该目录应包含
`manifest.json` 和 `vendor/`。按 C++ SDK 指南设置 SDK 路径环境变量。
从仓库根目录运行：

```bash
python3 tools/bazel_offline.py --output-user-root "$PWD/artifacts/bazel-output" \
  build //recipes/... //recipes/device-info:main_cpp //recipes/subscribe-state:main_cpp \
  //recipes/service-call:main_cpp //recipes/camera:main_cpp //recipes/audio:main_cpp \
  //recipes/locomotion:main_cpp //recipes/rcp-task:main_cpp
python3 tools/bazel_offline.py --output-user-root "$PWD/artifacts/bazel-output" \
  run //recipes/subscribe-state:main_cpp
```

离线时使用此入口替代直接调用 `bazel`。它在启动前检查包内文件哈希、当前仓库的
模块／锁文件哈希及 Bazel 版本；忽略环境中的 Bazel 配置，关闭 WORKSPACE 回退
和仓库下载，使用独立的输出／缓存目录。缺少依赖包时会在启动 Bazel 前报错。
上面的预览不会访问机器人；在线执行仍需满足各 Recipe 的设备环境和显式操作参数。

该入口不是任意构建规则或应用程序的网络沙箱，不会禁止 `bazel run` 启动的程序
使用网络。新增目标或构建配置可能需要重新生成依赖包。不要把工作站的 SDK 库
或生成的 CPU 配置用于不兼容的设备架构。

## 准备依赖包

在联网机器上准备好 SDK 路径及可选解码构建依赖后运行：

```bash
python3 tools/prepare_bazel_offline.py --output artifacts/offline/bazel
tar -czf artifacts/bazel-offline.tar.gz -C artifacts/offline/bazel .
sha256sum artifacts/bazel-offline.tar.gz
```

目标目录必须不存在。准备工具通过 Bazel 的
[vendor 模式](https://bazel.build/external/vendor)取得公开上游依赖，保留许可证，
生成带校验值的快照；本机平台检测结果会在使用机器上重新生成。
将压缩包和可信校验值与配套 SDK 一并交付；生成的依赖目录保留在发布包中，不加入 Git。

制作开发镜像时，将依赖包、wheelhouse、SDK、本机架构构建工具及可选解码依赖
一起打入镜像。分发前，用全新的输出／缓存目录，在无法访问外网的环境中检查构建。
已有缓存命中的构建结果不能代替对交付内容的验证。
