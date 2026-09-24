# 开放接口参考

<p align="center"><a href="README.md">English</a> | 中文</p>

通过[能力索引](../../catalog/README.zh-CN.md)选择相关接口并检查发布范围。
能力索引引用本章节的契约，不证明设备在线可用。

接口参考统一适配 `foot_quadruped` EDU 的机器人应用版本 **V1.6.0**，
组件配套与配置限制见[兼容矩阵](../compatibility.zh-CN.md)。

## Agent 扩展接口

[Agent 能力参考](agent/README.zh-CN.md)记录当前四足 EDU 范围的 HTTP MCP、设备端 Skills 和运行时 AGENTS.md，
包含[内容注入 API](agent/content-api.zh-CN.md)。
连接步骤、协议检查及排障方法见[接入指南](../guides/agent-integration.zh-CN.md)。
请根据设备的固件及运行时版本确认接口可用性。

## Aorta 与机器人接口

[Aorta／ROS 2 参考](aorta-ros2.zh-CN.md)列出开放 topic 集的通信原语、方向、Aorta／ROS 类型与映射，
并整理 service 和 RCP 任务 action。
CLI 发现与只读采样从[设备 shell 配置](../getting-started/device-environment.zh-CN.md)开始。
按下表选择功能域。各章统一说明用途、关键数据定义、读取流程与异常处理。
每个功能域在能力索引中保留一个入口，各路由仍有独立类型和使用条件；只检查任务实际需要的接口。

| 功能域 | 定义与使用指南 |
| --- | --- |
| 传感器 | [硬件遥测](sensors.zh-CN.md)：电池、IMU、雷达、UWB、GNSS、舵机反馈 |
| 相机 | [相机与 AprilTag](cameras.zh-CN.md)：标定、视频解码、标签结果 |
| Perception | [目标检测与人体关键点](perception.zh-CN.md)：人体出现与姿态交互输入 |
| Audio | [音频与语音输入](audio.zh-CN.md)：音频帧、ASR 文本、语音事件、输入结束 |
| 运动 | [状态、报告与控制](locomotion.zh-CN.md)：请求关联、区分输出与指令 |
| 系统与外设 | [系统、显示与灯光](system-peripherals.zh-CN.md)：状态解释、亮度控制 |
| RCP | [任务与追踪](rcp.zh-CN.md)：action 生命周期、取消、关联事件 |
| SLAM | [建图与定位](../guides/mapping-localization.zh-CN.md)：地图、位姿、变换与模式切换 |

字段定义见 [Schema](../../schemas/README.zh-CN.md)，可执行 Python 示例见 [Recipes](../../recipes/README.zh-CN.md)，
安装步骤见 [SDK 指南](../../packages/aorta/python/README.zh-CN.md)。详细 Aorta 接口页面应记录：

- 功能、开放状态、适用 `robot_type` 标识、具体型号／硬件版本及最低固件版本。
- 准确的 Aorta 路由、通信类型及开发者调用方向。
- Schema、字段语义、单位、坐标系与时间戳约定。
- 前置条件、超时、错误处理及资源清理。
- Python SDK 调用、可构建示例和验证结果。
- 如有 ROS2 映射，记录经过验证的名称；没有则明确标注不适用。

Schema / 注册信息是结构化事实的来源；行为与安全条件仍需人工维护。
