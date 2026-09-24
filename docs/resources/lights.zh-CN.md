# 灯光模式

<p align="center"><a href="lights.md">English</a> | 中文</p>

RGB 与 brightness 范围为 0–255，speed 是效果参数，不是秒或毫秒。

| typed LightMethod | DSL task |
| --- | --- |
| FIXED_COLOR | light.FIXEDCOLOR |
| GRADIENT | light.GRADIENT |
| BREATHING | light.BREATHING |
| FLASHING | light.FLASHING |
| CIRCLE_AND_FLASH | light.CIRCLEANDFLASH |
| PULSE | light.PULSE |

持续时间通过 DAG 生命周期或 DSL 的 `play_for_ms` 控制。普通用户使用 INTERACTION 层。

返回[设备资源](README.zh-CN.md)；通过 RCP 使用时见[节点字段参考](../interfaces/rcp-commands.zh-CN.md)。
