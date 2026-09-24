# 设备类型指南

<p align="center"><a href="README.md">English</a> | 中文</p>

按设备类型选择指南。当前 EDU 发布范围仅为四足机器狗，
四轮机器狗及双足机器人的 EDU 指南为后续版本预留。
机型专属目录名与构建系统中的标准 `robot_type` 标识一致。
`quadruped-common/` 存放两类机器狗共用的内容，不是构建标识。
这些标识用于选择文档，不能仅凭标识存在就认定已支持 EDU。

| 设备类型 | 构建标识／指南入口 | EDU 范围 | 文档状态 |
| --- | --- | --- | --- |
| 四足机器狗 | [foot_quadruped](foot_quadruped/README.zh-CN.md) | 当前发布对象 | 已有[共用连接指南](quadruped-common/connection.zh-CN.md)、shell 配置、硬件参考及接口流程；已有 Python/C++ Recipes |
| 四轮机器狗 | [wheel_quadruped](wheel_quadruped/README.zh-CN.md) | 后续发布 | 已有[共用连接指南](quadruped-common/connection.zh-CN.md)与硬件参考，未发布完整 EDU 指南 |
| 双足机器人 | [foot_humanoid](foot_humanoid/README.zh-CN.md) | 后续发布 | 预留入口；硬件参考及 EDU 指南待补充 |

具体产品型号、固件、SDK 与接口支持情况见[兼容矩阵](../compatibility.zh-CN.md)。

## 文档结构约定

- 通用章节：[快速开始](../getting-started/README.zh-CN.md)、
  [开发流程](../development/README.zh-CN.md)、[接口参考](../interfaces/README.zh-CN.md)
  及[功能指南](../guides/README.zh-CN.md)。公共流程在此维护，不按设备类型重复复制。
- 机器狗共用内容：[有线连接与 SSH 登录指南](quadruped-common/connection.zh-CN.md)
  在 `docs/robots/quadruped-common/` 维护，两类机器狗指南均链接至此；
  不适用于双足机器人，也不改变各类型的 EDU 发布状态。
- 机型专属内容：放在 `docs/robots/<robot_type>/`，用于连接差异、设备前置条件、
  可用接口、示例、部署差异和排障方法；随对应 EDU 版本接入、验证后逐步补齐章节。
- 硬件规格：仍放在 [docs/hardware/](../hardware/README.zh-CN.md)。
  两类机器狗引用同一份[共用传感器规格](../hardware/quadruped-common/sensors.zh-CN.md)
  和[背部安装／机械臂转接板参考](../hardware/quadruped-common/back-mounting.zh-CN.md)。
  双足机器人须提供独立审核的规格，不继承机器狗参数。
- 兼容性：分别记录设备类型、具体产品型号／硬件版本，以及固件／SDK 版本。
  类型相同或传感器相同都不能单独作为兼容性保证。

新增设备类型或变更发布状态时，同步更新本索引、机型指南、硬件适用范围索引和兼容矩阵的中英文版本。
若后续硬件版本出现差异，应新增明确命名、标注适用范围的规格文档，
不要静默覆盖共用参数，也不要把同一份参数复制到多个指南中。
