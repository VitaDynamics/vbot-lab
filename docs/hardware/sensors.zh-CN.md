# 传感器规格索引

<p align="center"><a href="sensors.md">English</a> | 中文</p>

请按设备类型选择规格。本索引保留原传感器文档路径，参数表仅在链接指向的硬件规格正文中维护。

| 设备类型 | 构建标识 | 传感器规格 | EDU 发布范围 |
| --- | --- | --- | --- |
| 四足机器狗 | `foot_quadruped` | [机器狗共用规格](quadruped-common/sensors.zh-CN.md) | 当前发布对象 |
| 四轮机器狗 | `wheel_quadruped` | [同一份机器狗共用规格](quadruped-common/sensors.zh-CN.md) | 后续发布；指南未发布 |
| 双足机器人 | `foot_humanoid` | 尚未整理，不使用机器狗参数 | 后续发布；指南未发布 |

共用规格覆盖所述机器狗硬件配置的双目模组、激光雷达、红外摄像头、UWB 雷达和 IMU。
共用传感器不代表固件、开放接口、SDK 兼容性或 EDU 开放状态相同。

执行设备开发流程前，请查看[设备类型指南](../robots/README.zh-CN.md)及
[兼容矩阵](../../release/compatibility.zh-CN.md)。
