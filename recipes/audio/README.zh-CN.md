# 读取音频与 ASR

<p align="center"><a href="README.md">English</a> | 中文</p>

[Recipes 索引](../README.zh-CN.md) · [Python](main.py) · [C++](main.cc)

接口: `/raw_audio_dump`, `/audio/uwb_adpcm_segment`, `/speech/asr_result`, `/uwb/audio_done` — pub/sub.

生成类型: `foxglove.RawAudio`, `aorta.topic.speech.AsrResult`, `aorta.uwb.AudioDoneEvent`.

`--source body` 读取本体麦克风；`--source uwb` 读取 UWB 信令携带的压缩音频（ADPCM、8 kHz、单声道）。本体流的编码、采样率和声道数应以消息为准，不能套用 UWB 编码。`--source asr` 读取识别文本：provider BODY=1 为本体麦克风，TAG=2 为 UWB，UNKNOWN=0 保持未知。`--provider body|tag` 只过滤 ASR，不过滤原始音频。`--source uwb-end` 读取输入传输结束事件及可选交互 ID，不代表识别完成或播放完成。

## Python：构建与离线预览

使用 `--output` 保存二进制音频时，需要 `numpy==2.2.6` 批量提取数据；按
[离线指南](../../docs/development/offline-build.zh-CN.md)准备匹配的 wheel。
仅订阅元数据或 ASR 不需要 NumPy。

```bash
bazel build //recipes/audio:main
bazel run //recipes/audio:main
```

默认只输出 JSON 请求计划，不安装 SDK、不连接设备、不发送请求。

## Python：在设备上运行

先完成 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)：传输本示例及配套 wheel，并在设备创建 venv。保持位于部署所得的应用目录（APP_DIR），激活该目录的 venv、配置设备环境后运行：

```bash
python -m recipes.audio.main --source asr --provider tag --consent --execute --count 1 --timeout 20
```

所有在线语音访问都需要参与者许可及 `--consent`。其他入口：

```bash
python -m recipes.audio.main --source body --consent --execute --count 10
python -m recipes.audio.main --source uwb --consent --execute --count 10 --output uwb.adpcm > uwb.frames.jsonl
python -m recipes.audio.main --source uwb-end --consent --execute --timeout 20
```

二进制输出只是拼接的载荷字节，不是 WAV、解码后的 PCM，也不保证包含完整话语。应保留配套 JSONL 元数据（偏移、长度和时间戳），以恢复帧边界；录制遇到编码、采样率或声道变化会报错。UWB 输入结束事件是独立订阅，完整应用应在输入前同时建立两个订阅，并利用可用的交互上下文；这里的短命令不重建完整录音会话。未知 ASR provider 不会被归为 BODY 或 TAG。

## C++

先按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)准备配套 SDK／Schema 压缩包与编译环境，设置两个发布制品路径。在构建机上显式构建 C++ 目标，预览也需要链接 SDK，但不会创建 Node 或访问设备：

```bash
bazel build //recipes/audio:main_cpp
bazel run //recipes/audio:main_cpp
```

按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md#在机器人上运行)设置 RECIPE=audio 并完成部署。以 vbot 身份 SSH 登录后，进入部署所得应用目录，按流程配置 shell 和动态库路径，满足上面的任务前提后直接运行可执行文件：

```bash
./bin/audio --source asr --provider tag --consent --execute --count 1 --timeout 20
```

设备无需 Bazel、编译器或仓库副本。C++ 使用与 Python 相同的路由、操作许可和完成条件；只读订阅不会发布指令。

C++ 也按同一来源规则输出帧元数据、ASR provider 或输入结束事件；保留 JSONL 与二进制文件以恢复帧边界：

```bash
./bin/audio --source body --consent --execute --count 10
./bin/audio --source uwb --consent --execute --count 10 --output uwb.adpcm > uwb.frames.jsonl
./bin/audio --source uwb-end --consent --execute --timeout 20
```

## 完成、失败与退出

输出为逐行 JSON；退出码 0 表示完成本示例的操作（离线预览也返回 0），1 表示运行失败或超时，2 表示参数不合法，130 表示中断。检查 execute 参数和输出语义，不要把离线预览视为在线成功。所有等待都有上限；订阅队列溢出会报错，不把丢失样本当完整数据。退出时关闭订阅、客户端及 Node。

文件只会新建，不覆盖已有路径；每个样本最多 8 MiB，总捕获最多 16 MiB。失败或中断可能保留部分文件，需按错误输出判断，并按隐私要求手动保留或删除。

测试说明见 [Recipes](../README.zh-CN.md)；默认测试不连接或操作设备。
