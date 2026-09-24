# Light modes

<p align="center">English | <a href="lights.zh-CN.md">中文</a></p>

RGB and brightness range from 0 to 255; speed is an effect parameter, not seconds or milliseconds.

| typed LightMethod | DSL task |
| --- | --- |
| FIXED_COLOR | light.FIXEDCOLOR |
| GRADIENT | light.GRADIENT |
| BREATHING | light.BREATHING |
| FLASHING | light.FLASHING |
| CIRCLE_AND_FLASH | light.CIRCLEANDFLASH |
| PULSE | light.PULSE |

Control the hold using DAG lifecycle or DSL `play_for_ms`. Use INTERACTION for ordinary user layers.

Back to [device resources](README.md); for RCP use, see the [node command reference](../interfaces/rcp-commands.md).
