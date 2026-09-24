# 读取相机图像

<p align="center"><a href="README.md">English</a> | 中文</p>

[Recipes 索引](../README.zh-CN.md) · [Python](main.py) · [C++](main.cc)

接口: `/image_left_raw/h265`, `/image_right_raw/h265` — pub/sub.

生成类型: `foxglove.CompressedVideo`.

选择单路相机，输出编码、frame ID、采集时间戳和载荷长度。载荷是 H.265 Annex B 视频流，不是 JPEG 或 RGB。默认仅读取元数据；获得许可后，可保存压缩字节到新文件，或用 `--decode` 获取内存中的 RGB 图像。每路相机独立使用解码器；解码依赖关键帧与 VPS/SPS/PPS，中途订阅可能暂时没有可解码图像。

## Python：构建与离线预览

```bash
bazel build //recipes/camera:main
bazel run //recipes/camera:main
```

默认只输出 JSON 请求计划，不安装 SDK、不连接设备、不发送请求。

## Python：在设备上运行

先完成 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)：传输本示例及配套 wheel，并在设备创建 venv。保持位于部署所得的应用目录（APP_DIR），激活该目录的 venv、配置设备环境后运行：

```bash
python -m recipes.camera.main --camera left --execute --count 60 --timeout 10
```

可选图像解码：按 [离线指南](../../docs/development/offline-build.zh-CN.md)，将匹配架构的
wheel 放入 `artifacts/wheelhouse`，再安装到执行机器的 venv。二进制保存同样需要 NumPy
批量提取载荷：

```bash
python -m pip install --no-index --find-links artifacts/wheelhouse av==16.1.0 numpy==2.2.6
python -m recipes.camera.main --camera left --execute --count 120 --timeout 20 --decode --consent
python -m recipes.camera.main --camera left --execute --count 120 --timeout 20 --output left.h265 --consent
```

解码器调用 `frame.to_rgb()`；通过 `bytes(rgb.planes[0])` 访问像素，并按 `plane.line_size` 处理行填充。输出解码后的宽、高、像素格式和行跨度。在上限内没有解码出图像会报错，不算成功。保存的流开头可能早于可用关键帧。本示例不实现双目同步，也不导出图片文件。人体检测优先使用内置[感知输出](../../docs/interfaces/perception.zh-CN.md)，无需先解码并部署新模型。

## C++

先按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)准备配套 SDK／Schema 压缩包与编译环境，设置两个发布制品路径。在构建机上显式构建 C++ 目标，预览也需要链接 SDK，但不会创建 Node 或访问设备：

```bash
bazel build //recipes/camera:main_cpp
bazel run //recipes/camera:main_cpp
```

按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md#在机器人上运行)设置 RECIPE=camera 并完成部署。以 vbot 身份 SSH 登录后，进入部署所得应用目录，按流程配置 shell 和动态库路径，满足上面的任务前提后直接运行可执行文件：

```bash
./bin/camera --camera left --execute --count 60 --timeout 10
```

设备无需 Bazel、编译器或仓库副本。C++ 使用与 Python 相同的路由、操作许可和完成条件；只读订阅不会发布指令。

基础 `:main_cpp` 只依赖 Aorta SDK，可通过 `--output left.h265 --consent` 保存压缩字节，
不会把 H.265 当作 RGB。C++ 解码使用 [FFmpeg 构建前提](../../packages/aorta/cpp/README.zh-CN.md)中的可选目标，
在构建机生成 `:main_cpp_decode`，将其以 `bin/camera-decode` 名称连同 FFmpeg 运行库部署后，在已配置的设备上执行：

```bash
./bin/camera-decode --camera left --decode --consent --execute --count 120 --timeout 20
```

[decoder.h](decoder.h) 中的 `rgb` 是连续 RGB24 字节，行跨度为宽度乘 3；
使用或移交该缓冲区后再离开当前帧作用域。每路相机独立解码，结束时排空延迟帧，
未解码出图像时报错；本例不保存图片或进行双目同步。

## 完成、失败与退出

输出为逐行 JSON；退出码 0 表示完成本示例的操作（离线预览也返回 0），1 表示运行失败或超时，2 表示参数不合法，130 表示中断。检查 execute 参数和输出语义，不要把离线预览视为在线成功。所有等待都有上限；订阅队列溢出会报错，不把丢失样本当完整数据。退出时关闭订阅、客户端及 Node。

文件只会新建，不覆盖已有路径；每个样本最多 8 MiB，总捕获最多 16 MiB。失败或中断可能保留部分文件，需按错误输出判断，并按隐私要求手动保留或删除。

测试说明见 [Recipes](../README.zh-CN.md)；默认测试不连接或操作设备。
