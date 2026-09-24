# 在 Foxglove 中查看 Aorta topic

<p align="center"><a href="foxglove.md">English</a> | 中文</p>

以 `vbot` 身份在机器人上运行 `aorta-foxglove-bridge`，再从电脑上的 Foxglove
通过 WebSocket 连接。这是原生 Aorta topic 查看入口，与 ROS 2 兼容桥不同；
设备不需要仓库副本、SDK 安装、Docker 或 Bazel。

查看机器人几何、关节或 URDF 文件时，可使用不需要实时设备连接的
[Vbot Viewer](vbot-viewer.zh-CN.md)。它是模型工具，不是实时 topic 查看器。

## 1. 连接设备并准备 shell

先按[设备连接与 SSH 登录](../robots/quadruped-common/connection.zh-CN.md)进入设备。
以下命令在**设备 SSH shell** 执行，不在 host 或开发容器中执行：

```bash
whoami
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
command -v aorta-foxglove-bridge
test -r "$ZENOH_SESSION_CONFIG_URI"
```

应输出 `vbot`、可解析的 bridge 可执行文件路径，且配置文件可读检查成功。
任一检查失败则停止并确认设备工具是否已提供，不修改权限。
PATH 用于找到可执行文件；ZENOH_SESSION_CONFIG_URI 选择随设备交付的 EDU 会话配置。
启动命令还会通过 `--zenoh-config` 显式传入同一路径。
原生 bridge 不需要加载 ROS setup，也不需要设置 RMW_IMPLEMENTATION、ROS_DOMAIN_ID 或
ROS_LOCALHOST_ONLY。持久化 shell 设置见[设备环境](../getting-started/device-environment.zh-CN.md)。
非交互启动脚本应自行导出上述环境，不假定交互式 `.bashrc` 已加载。

## 2. 启动 bridge

下面两种命令都包含音频、ASR 与相机流。启动前应取得被采集人员的音视频授权。即使尚无
查看客户端连接，bridge 也会订阅数据。查看期间保持终端打开。

### 使用发布的配置

带 EDU 路由器的机器人软件会发布 `/opt/vita/aorta/edu/foxglove_bridge.yaml`。它选中
EDU 程序可读取的全部机器人话题，以及你自己的 EDU 程序发布的全部话题：

```bash
aorta-foxglove-bridge \
  --config /opt/vita/aorta/edu/foxglove_bridge.yaml \
  --host 192.168.126.2 \
  --port 8765 \
  --server-name edu-vbot
```

话题在收到第一条消息后才会出现在 Foxglove 中。如果该文件不存在，说明机器人软件没有
EDU 路由器，请使用下面的话题列表。

### 使用话题列表

只列出需要的话题以降低设备和网络负载，尤其避免同时订阅多种视频分辨率与大量点云。
不需要音频、ASR 与相机数据时移除对应项。

```bash
aorta-foxglove-bridge \
  --group default \
  --zenoh-config /opt/vita/aorta/edu/edu_session.json5 \
  --host 192.168.126.2 \
  --port 8765 \
  --server-name edu-vbot \
  --include audio/uwb_adpcm_segment \
  --include bms_state \
  --include display_node/status \
  --include gnss/fix \
  --include gnss/fusion \
  --include image_left_raw/h265 \
  --include image_left_raw/h265_half \
  --include image_left_raw/h265_quarter \
  --include image_left_raw/h265_undistort \
  --include image_right_raw/h265 \
  --include image_right_raw/h265_half \
  --include image_right_raw/h265_quarter \
  --include imu_raw \
  --include lidar_diagnostic_status \
  --include lidar_imu \
  --include lidar_packets \
  --include lidar_points \
  --include light/ear_modulation \
  --include locomotion/action_report \
  --include locomotion/body/task_report \
  --include locomotion/body_action_status \
  --include locomotion/event \
  --include locomotion/head/task_report \
  --include locomotion/head_status \
  --include locomotion/joy \
  --include locomotion/status \
  --include locomotion/velocity_command \
  --include lowlevel/servo_status \
  --include odometry \
  --include perception/detections2d \
  --include perception/poses \
  --include raw_audio_dump \
  --include rcp/trace \
  --include slam/grid_map/compressed \
  --include slam/static_transforms \
  --include slam/status \
  --include speech/asr_result \
  --include stereo_apriltag/detection \
  --include stereo_left/camera_info \
  --include stereo_right/camera_info \
  --include system/sm_status \
  --include uwb/audio_done \
  --include uwb/head_touch \
  --include uwb/ranging \
  --include uwb/state \
  --include voice/event
```

- `--group default`：选择 Aorta group。
- `--host`：机器人本机监听地址，不是电脑地址。有线连接使用文档中的 `192.168.126.2`；
  使用其他连接方式时，改为实际配置在机器人网卡上、且电脑可访问的地址。
- `--port 8765`：WebSocket 端口。已占用时选择空闲端口并同步修改客户端 URL，
  不停止无关进程。
- `--server-name edu-vbot`：显示名称，可替换为便于识别的名称。
- 多个 `--include`：使用不带前导斜杠的 topic 后缀，例如 Aorta `/imu_raw` 对应
  `imu_raw`。用于选择已发布的 topic 流，不是 ROS topic 映射、service 调用或 RCP 任务提交。
- include 缩小发布 topic 范围，但不是网络安全边界，也不筛除 bridge 的上下文／遥测通道。
  不要将监听端口暴露到不可信网络或转发到互联网。

`locomotion/joy`、`locomotion/velocity_command` 和 `light/ear_modulation`
等指令 topic 在这里仅作为消息观察，列入 include 不会发送控制指令。
类型与含义见[接口参考](../interfaces/README.zh-CN.md)。
配置中的 topic 可以处于空闲状态；include 不会启动生产者，也不保证有数据。

## 3. 从 Foxglove 连接

在电脑上的 Foxglove 打开 **Foxglove WebSocket** 连接，地址为 `ws://192.168.126.2:8765`。
应与上一步监听地址、端口一致；bridge 在机器人上运行时，不要填写电脑的 `localhost`。

先在 Raw Messages 中选择可用通道查看解码字段，再选择合适的曲线或可视化面板。
发现通道不等于收到消息，应观察数据值／时间戳是否更新。
图像显示还取决于消息 Schema 与编码支持；H.265 流是压缩视频，不是原始 RGB。

### Foxglove 中的 topic 命名

bridge 使用 **完整 Aorta 传输 key** 作为 Foxglove 通道的 topic 名，
不是 Aorta API 中的短名称，也不是 ROS 2 映射后的名称：

```text
Aorta topic:       /<topic>
CLI filter:        --include <topic>
Foxglove topic:    aorta/<group>/pub/<topic>
```

以上文的 `--group default` 为例：

| Aorta topic | `--include` 参数值 | Foxglove topic |
| --- | --- | --- |
| `/imu_raw` | `imu_raw` | `aorta/default/pub/imu_raw` |
| `/locomotion/status` | `locomotion/status` | `aorta/default/pub/locomotion/status` |
| `/image_left_raw/h265` | `image_left_raw/h265` | `aorta/default/pub/image_left_raw/h265` |
| `/perception/detections2d` | `perception/detections2d` | `aorta/default/pub/perception/detections2d` |
| `/audio/uwb_adpcm_segment` | `audio/uwb_adpcm_segment` | `aorta/default/pub/audio/uwb_adpcm_segment` |
| `/slam/static_transforms` | `slam/static_transforms` | `aorta/default/pub/slam/static_transforms` |

在 Foxglove 的 topic 选择器及保存的布局中使用完整名称，`aorta/` 前**没有前导斜杠**。
`pub` 表示发布 topic 的命名空间，不表示可以发送控制指令。
更换 group 会改变名称中的 group 段；`--server-name` 只修改服务显示名称，不改变 topic 名。
特别是 `/slam/static_transforms` 在这里不会变成 ROS 2 的 `/tf_static`。

其他可用通道保留各自的命名空间：上下文为 `aorta/<group>/ctx/<path>`，
遥测为 `aorta/<group>/sys/telemetry/<path>`。不要为它们添加 `pub/`，
也不要与发布 topic 的 `--include` 参数值混淆。

消息 Schema 名称（例如 `foxglove.RawAudio`）描述载荷类型，不是 topic 名。
Schema 缺失也不会改变通道名称。

## 4. 停止与排障

在 bridge 所在的设备终端按 Ctrl+C 停止。本前台运行流程不配置自启动，也不修改系统服务。

| 现象 | 检查方向 |
| --- | --- |
| 找不到可执行文件 | 设备工具是否已提供，同一 shell 的 PATH 是否正确 |
| 会话／配置错误 | EDU 会话路径可读，显式配置路径正确 |
| 无法绑定地址 | 地址是否属于机器人当前网卡 |
| 地址已被占用 | 改用空闲端口并同步修改查看端 URL |
| 电脑无法连接 | 设备 IP、接线／网络路由、端口和 bridge 进程 |
| 有通道但没有样本 | 生产者状态和接口前提；不要仅为制造数据而发送运动指令 |
| Raw Messages 有数据但面板为空 | 消息 Schema、编码与面板支持情况 |
| 负载较高或显示延迟 | 移除无关 include，避免同时订阅多种视频流，缩小范围后重新连接 |

排障信息中不要复制会话配置内容或凭据。
