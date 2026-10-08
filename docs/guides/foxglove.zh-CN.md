# 在 Foxglove 中查看 Aorta topic

<p align="center"><a href="foxglove.md">English</a> | 中文</p>

以 `vbot` 身份在机器人上运行 `aorta-foxglove-bridge`，再从电脑上的 Foxglove
通过 WebSocket 连接。这是原生 Aorta topic 查看入口，与 ROS 2 兼容桥不同；
设备不需要仓库副本、SDK 安装、Docker 或 Bazel。

查看机器人几何、关节或 URDF 文件时，可使用不需要实时设备连接的
[Vbot Viewer](vbot-viewer.zh-CN.md)。它是模型工具，不是实时 topic 查看器。

启动 bridge 前，先选择连接方式：

| 连接方式 | bridge 在机器人上监听 | Foxglove 在电脑上连接 |
| --- | --- | --- |
| 有线直连 | `192.168.126.2:8765` | `ws://192.168.126.2:8765` |
| Wi-Fi，经 SSH 隧道 | `127.0.0.1:8765` | 启动隧道后连接 `ws://127.0.0.1:8765` |

机器人的 Wi-Fi IP 是 **SSH 入口地址**，不一定属于运行 bridge 的设备 shell 所在网卡，
不要直接将它替换到 `--host` 中。隧道通过 SSH 承载 WebSocket 连接，
无需在 Wi-Fi 网络上另行开放 WebSocket 端口。

## 1. 连接设备并准备 shell

先以 `vbot` 账户建立 SSH 连接。有线方式见
[设备连接与 SSH 登录](../robots/quadruped-common/connection.zh-CN.md)。
使用 Wi-Fi 时，机器人应已联网，且电脑能够访问它当前分配到的 IP。
复用可用的公钥登录配置，或先完成上述链接中的公钥配置步骤。
在**电脑终端**中，将占位符替换为机器人的实际 Wi-Fi IP：

```bash
ROBOT_SSH_TARGET='vbot@<robot-wifi-ip>'
ssh "$ROBOT_SSH_TARGET"
```

如果已为这台机器人的 `vbot` 账户配置 SSH 别名，可将 `ROBOT_SSH_TARGET` 改为该别名；
下文创建隧道的终端也使用相同目标。设备 shell 与隧道必须连接同一个 SSH 目标。
登录失败时，先解决网络、认证或主机密钥问题，再继续操作；不要关闭主机密钥检查。

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
使用话题列表的命令还会通过 `--zenoh-config` 显式传入同一路径。
原生 bridge 不需要加载 ROS setup，也不需要设置 RMW_IMPLEMENTATION、ROS_DOMAIN_ID 或
ROS_LOCALHOST_ONLY。持久化 shell 设置见[设备环境](../getting-started/device-environment.zh-CN.md)。
非交互启动脚本应自行导出上述环境，不假定交互式 `.bashrc` 已加载。

## 2. 启动 bridge

选择下列一种启动方式，不要在同一端口启动多个 bridge。
即使尚无查看客户端连接，bridge 也会订阅数据。查看期间保持此设备终端打开。

### Wi-Fi：监听回环地址

在上一步准备好的设备 shell 中，先选择少量只读数据：

```bash
aorta-foxglove-bridge \
  --group default \
  --zenoh-config /opt/vita/aorta/edu/edu_session.json5 \
  --host 127.0.0.1 \
  --port 8765 \
  --server-name edu-vbot \
  --include bms_state \
  --include imu_raw \
  --blacklist-full 'aorta/*/ctx/**' \
  --blacklist-full 'aorta/*/sys/telemetry/**' \
  --ctx-snapshot-interval-ms 0
```

此命令选择电池和 IMU 话题，排除上下文／遥测通道并关闭上下文快照，
不订阅音频或相机话题。保持 bridge 运行，再按第 3 节创建 SSH 隧道。
此流程不需要修改系统服务或网络转发规则。

### 有线：使用发布的配置

此配置和下面的完整话题列表都包含音频、ASR 与相机流。
使用这两种方式前，应取得被采集人员的音视频授权。

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

### 有线：使用话题列表

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
  SSH 隧道使用 `127.0.0.1`。Wi-Fi SSH 入口 IP 不能直接替代这两个监听地址。
- `--port 8765`：WebSocket 端口。已占用时选择空闲端口，并相应修改直连客户端 URL
  或隧道的设备目标端口；不停止无关进程。
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

### 有线直连

在电脑上的 Foxglove 打开 **Foxglove WebSocket** 连接，地址为 `ws://192.168.126.2:8765`。
未使用隧道时，应填写电脑可访问的设备监听地址，不是电脑的 `localhost`。

### Wi-Fi，经 SSH 隧道连接

保持第一个终端中的 bridge 运行。在**运行 Foxglove 的同一台电脑上打开第二个终端**，
不要在设备 SSH shell 或开发容器中执行。将占位符替换为首次登录时使用的 Wi-Fi IP，
或复用相同的 SSH 别名：

```bash
ROBOT_SSH_TARGET='vbot@<robot-wifi-ip>'
ssh -N -T -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:8765:127.0.0.1:8765 "$ROBOT_SSH_TARGET"
```

第一个 `127.0.0.1:8765` 是电脑上的本地监听地址；第二个是从 SSH 服务端访问的
机器人回环地址与 bridge 端口。`-N -T` 不打开远程 shell，也不分配终端，
不会替你启动 bridge。命令保持运行、没有持续输出是正常现象。两个终端都需保持打开。

在 Foxglove 中选择 **Foxglove WebSocket**，连接 `ws://127.0.0.1:8765`。
当 `localhost` 解析为 IPv4 回环地址时，也可使用 `ws://localhost:8765`；
如果它解析为 `::1`，请改用上述明确的 IPv4 地址。此流程不连接 Wi-Fi IP 的 8765 端口。

如果**电脑上的** 8765 端口已被占用，可改用其他本地端口：

```bash
ssh -N -T -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:18765:127.0.0.1:8765 "$ROBOT_SSH_TARGET"
```

此时 Foxglove 改连 `ws://127.0.0.1:18765`，设备 bridge 仍使用 8765。
若修改的是**设备端口**，应同时修改 `--port` 和 `-L` 最右侧的端口。
本地转发保持绑定 `127.0.0.1`，不要改成 `0.0.0.0`，避免其他电脑访问此转发入口。
`ExitOnForwardFailure` 能发现建立转发监听失败，但不代表远端 bridge 已运行或话题已有数据。

### 确认消息到达

先在 Raw Messages 中选择可用通道查看解码字段，再选择合适的曲线或可视化面板。
发现通道不等于收到消息，应观察数据值／时间戳是否更新。
图像显示还取决于消息 Schema 与编码支持；H.265 流是压缩视频，不是原始 RGB。
上面的 Wi-Fi 最小选择可查看 `aorta/default/pub/bms_state` 和
`aorta/default/pub/imu_raw`，应能看到电池字段和持续更新的 IMU 时间戳；
仅连接成功或出现通道名还不够。需要其他话题时，先停止 bridge，再参考上面的列表调整
include，隧道方式继续保留 `--host 127.0.0.1`。加入音频或相机流前需取得相应授权。
也可以将使用发布配置的启动命令改为 `--host 127.0.0.1` 后通过隧道查看，
其话题选择范围仍为第 2 节所述的全部话题。

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

先断开 Foxglove，再在使用中的隧道终端和 bridge 所在的设备终端分别按 Ctrl+C。
停止隧道不会停止 bridge，停止 bridge 也不会关闭隧道。
本前台运行流程不配置自启动，也不修改系统服务。

| 现象 | 检查方向 |
| --- | --- |
| 找不到可执行文件 | 设备工具是否已提供，同一 shell 的 PATH 是否正确 |
| 会话／配置错误 | EDU 会话路径可读，显式配置路径正确 |
| 无法绑定地址 | 有线方式检查设备网卡地址；隧道方式使用 `--host 127.0.0.1`，而非 Wi-Fi 入口 IP |
| 地址已被占用 | 先区分电脑端口与设备端口，再调整对应端口及 URL，不停止无关进程 |
| 电脑无法连接 | 设备 IP、接线／网络路由、端口和 bridge 进程 |
| 隧道提示 `connect failed: Connection refused` | bridge 是否在同一 SSH 目标上运行，并监听 `-L` 右侧指定的回环地址和端口 |
| 隧道提示 `administratively prohibited` | 当前 SSH 入口的转发策略；停止并联系支持，不修改设备权限或 SSH 服务配置 |
| 隧道保持运行，但 Foxglove 无法连接 | 是否在同一台电脑连接本地转发端口；尝试用 `127.0.0.1` 替代 `localhost`，并确认远端 bridge 仍在运行 |
| 有通道但没有样本 | 生产者状态和接口前提；不要仅为制造数据而发送运动指令 |
| Raw Messages 有数据但面板为空 | 消息 Schema、编码与面板支持情况 |
| 负载较高或显示延迟 | 移除无关 include，避免同时订阅多种视频流，缩小范围后重新连接 |

排障信息中不要复制会话配置内容或凭据。
