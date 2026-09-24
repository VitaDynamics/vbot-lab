# 四轮机器狗 EDU — 后续发布

<p align="center"><a href="README.md">English</a> | 中文</p>

- 构建标识：`wheel_quadruped`。
- EDU 范围：为后续版本预留，不在当前 EDU 发布范围内。
- 指南状态：已有共用连接指南与硬件参考，完整 EDU 开发指南尚未发布。

## 有线连接与 SSH 登录

本类型与 `foot_quadruped` 的连接方式相同，请按[共用连接指南](../quadruped-common/connection.zh-CN.md)
完成转接头连接、电脑网卡配置及 `vbot` 账户 SSH 登录。
共用连接步骤不扩大当前 EDU 发布范围，也不代表固件、SDK 或 API 兼容。

## 已有硬件参考

本类型与 `foot_quadruped` 共用以下硬件参考：

- [机器狗传感器规格](../../hardware/quadruped-common/sensors.zh-CN.md)。
- [背部安装尺寸与机械臂转接板](../../hardware/quadruped-common/back-mounting.zh-CN.md)：
  共用安装尺寸、CAD 文件与图示紧固件。

硬件参数适用情况与 EDU SDK、固件、开放接口和示例的可用性分别管理。

不能因为硬件相同，就直接套用四足机器狗的固件、部署操作或运动控制示例。

## 开发指南可用性

本类型支持的接口、Schema 及可运行示例尚未提供。
开始设备开发前，请在[兼容矩阵](../../compatibility.zh-CN.md)核对型号、固件与 SDK 支持情况。

返回[设备类型指南索引](../README.zh-CN.md)。
