# 相机、标定与 AprilTag

<p align="center"><a href="cameras.md">English</a> | 中文</p>

本功能域用于图像接收／解码、带标定的图像处理和标签交互。

Python SDK 实现见 [camera Recipe](../../recipes/camera/README.zh-CN.md)，包含源码、Bazel 目标、离线预览与显式设备运行。接口语义以下文为准。
下方 topic 表列出 `foot_quadruped` EDU 的只读 pub/sub 输出。
登录并完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)，
准确的 Aorta／ROS 消息类型及映射见[接口表](aorta-ros2.zh-CN.md)。

## 路由与数据含义

| Aorta topic | 含义 | 用法 |
| --- | --- | --- |
| `/stereo_left/camera_info`、`/stereo_right/camera_info` | 图像尺寸、`distortion_model`、`d`、`k`、`r`、`p`、binning 和 ROI | 选择与相机及图像几何对应的标定 |
| `/image_left_raw/h265`、`/image_right_raw/h265` | 左／右相机压缩视频 | 只解码应用需要的一路 |
| `/image_left_raw/h265_half`、`/image_right_raw/h265_half` | half 视频流变体 | 按实际解码尺寸选择，不预设分辨率 |
| `/image_left_raw/h265_quarter`、`/image_right_raw/h265_quarter` | quarter 视频流变体 | 适合时用于低分辨率图像处理 |
| `/image_left_raw/h265_undistort` | 左相机去畸变视频 | 使用匹配的校正后相机模型，不重复应用原始图像畸变 |
| `/stereo_apriltag/detection` | 左右有效位、标签 ID、判决裕量、角点、相机参数及坐标系标识 | 直接读取标签检测结果，不是人体检测 |

## 理解消息

- 视频包含 `timestamp`、`frame_id`、`format` 与压缩 `data`，不是 RGB 数组或 MP4 文件。
  H.265 数据采用 Annex B NAL 单元，解码器需要 VPS/SPS/PPS 参数和合适的关键帧。
  每路流保持独立解码状态，单个差分帧不一定能独立解码。图像尺寸取自解码流，不是此消息的字段。
- 标定 `k`、`r` 为行优先 3×3 矩阵，`p` 为 3×4，`d` 由畸变模型决定。
  相机光学坐标轴为右／下／前（+x/+y/+z）。
  对缩放或裁剪图像使用标定前，先检查尺寸、binning 与 ROI。
- 标签结果分别使用 `left_valid`、`right_valid`，仅在对应侧有效时读取标签 ID／角点。
  判决裕量不是人体检测置信度。标签消息本身不提供机器人米制位姿；
  估算位姿还需要标签实际尺寸、匹配的标定和坐标变换。

## JPEG 单帧尺寸约束

`/get_jpeg_images` 服务中，请求项的 `width` 和 `height` 是
**选择参考，不保证返回该分辨率**。相机会在已启用的 VSE（图像缩放输出）通道中，
按 `abs(requested_width - channel_width) + abs(requested_height - channel_height)`
最小的规则选择最接近的通道，而不是将 JPEG 任意缩放到请求尺寸。

应以各响应项的实际 `width`、`height` 为准，并核对它们与 JPEG 解码尺寸一致。
例如，请求 640×360 时，若选中的已启用输出为 480×270，可以返回可解码的 480×270 图像。
这种请求与响应的尺寸差异本身符合通道选择规则，**不能据此判定 Aorta／ROS 2 Bridge 故障**。
可用输出尺寸取决于相机配置，此例不表示固定的请求／响应尺寸映射。

先检查响应项 `status` 并解码 `data`，再进行图像处理。
缓冲区分配、像素坐标解释及标定选择均使用实际返回的图像几何。
应用需要严格固定输入尺寸时，在应用侧显式缩放解码图像，并相应调整像素坐标与相机内参。
解码失败、状态异常、响应尺寸与解码尺寸不一致，需要单独排查，
不要与请求尺寸和响应尺寸不同混为一谈。
字段见 [JPEG 请求与响应 schema](../../schemas/aorta/schemas/service/stereo/get_jpeg_images.fbs)。

## 最小读取与应用流程

无需打印视频载荷即可检查元数据与标定：

```bash
timeout 15s aorta topic list
timeout 15s aorta schema get /image_left_raw/h265 --describe
timeout 15s aorta schema get /stereo_left/camera_info --describe
timeout 15s aorta topic echo /stereo_left/camera_info --count 1
```

标签交互改为检查并读取处理后的输出：

```bash
timeout 15s aorta schema get /stereo_apriltag/detection --describe
timeout 15s aorta topic echo /stereo_apriltag/detection --count 1
```

1. 选择一路图像流，建立有界订阅，并在实际运行架构上初始化兼容的 H.265 解码器。
   仅发现元数据不能检查解码。
2. 等待编码初始化数据及可解码帧。将帧时间戳、尺寸、坐标系标识与对应标定关联；
   双目图像按采集时间配对，不按到达顺序配对，不混合两个相机的字节流。
3. 使用有界队列处理当前帧。丢包或重连后在合适的关键帧重新同步解码器，不展示损坏或过期帧。
4. 退出时关闭解码器和订阅。记录人物或保留图像前取得同意。
   [人体检测](perception.zh-CN.md)优先使用内置处理结果，除非应用确实需要图像或另一种模型。

## 输出缺失或不可用时

检查路由／类型发现、相机活动、帧与标定尺寸匹配情况及编码参数。
没有有效标签结果可能只是画面中没有支持的标签。
视频路由存在但无法解码时，先检查解码支持与码流初始化，不先修改设备配置。
退出码 `124` 表示限时等待结束，不证明相机故障，也不代表已解码出图像。
