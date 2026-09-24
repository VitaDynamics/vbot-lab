# 硬件参考

<p align="center"><a href="README.md">English</a> | 中文</p>

硬件规格描述机器人实际搭载的部件及其参数，与运行配置、标定数据和软件接口契约分别维护。

- [传感器规格索引](sensors.zh-CN.md)：按设备类型说明参数适用情况与发布范围。
- [机器狗共用传感器规格](quadruped-common/sensors.zh-CN.md)：`foot_quadruped` 与 `wheel_quadruped`
  共用的一套参数，覆盖双目模组、激光雷达、红外摄像头模组、UWB 雷达和 IMU。
- [机器狗共用背部安装尺寸与机械臂转接板](quadruped-common/back-mounting.zh-CN.md)：
  `foot_quadruped` 与 `wheel_quadruped` 共用的背部孔位尺寸、转接板图纸／STEP 及图示紧固件。

共用规格不适用于 `foot_humanoid`，其硬件文档待补充。
可复用规格在此维护，由[设备类型指南](../robots/README.zh-CN.md)引用。
每份规格须记录适用设备类型、产品型号及硬件版本。
出现硬件差异时新增独立适用范围的规格，不重复复制或静默替换共用数据。

软件访问方式见[接口参考](../interfaces/README.zh-CN.md)。
硬件规格本身不代表对应 SDK 接口已经开放。
