# Shared sensor specifications for robot dogs

<p align="center">English | <a href="sensors.zh-CN.md">中文</a></p>

The sensor hardware parameters for the robot-dog configurations below are listed here.
This is a hardware reference, not a runtime configuration or calibration file.

## Applicable robot types

| Robot type | Build identifier | Applicability |
| --- | --- | --- |
| Four-legged robot dog | `foot_quadruped` | Applies to the documented hardware configuration |
| Four-wheeled robot dog | `wheel_quadruped` | Shares this sensor specification; its EDU guide is not released |
| Bipedal robot | `foot_humanoid` | Not applicable; separate specifications are pending |

This page is the single shared specification for the two robot-dog types, not a
specification for all EDU robots. Exact product models and hardware revisions still
need to be identified before treating other configurations as equivalent.
Hardware applicability does not extend the current EDU release beyond `foot_quadruped`.
See the [robot-type guide index](../../robots/README.md) for release scope and guide status.

## Stereo camera module

| Parameter | Specification |
| --- | --- |
| Mounting location | Head |
| Resolution | 1920 (H) × 1080 (V) |
| Field of view (FOV) | 150° (horizontal) × 80° (vertical) |
| Stereo baseline | 70 mm |

## LiDAR

| Parameter | Specification |
| --- | --- |
| Mounting location | Head |
| Number of scan lines | 16 |
| Measurement range | 0.2–40 m |
| Horizontal FOV | 360° |
| Vertical FOV | 40.5° (−0.25° to +40.25°) |
| Laser wavelength | 905 nm |

## Infrared camera module

| Parameter | Specification |
| --- | --- |
| Mounting location | Underside of the abdomen |
| Output resolution | 1536 × 1160 |
| FOV | 88° × 68° |

The horizontal and vertical axis assignments for the infrared camera FOV are not specified.
Do not assume an axis assignment from the order of the values above.

## UWB radar

| Parameter | Specification |
| --- | --- |
| Mounting location | Head |
| FOV | 360° horizontal |

## IMU

| Parameter | Specification |
| --- | --- |
| Mounting location | Abdomen, S100 |

## Scope and limitations

- Sensor part numbers, hardware revisions, frame rates, accuracy, calibration data,
  and software interface names are not specified on this page.
- Sensor presence and hardware specifications do not imply public API availability.
  See the [interface reference](../../interfaces/README.md) for software access and the
  [compatibility matrix](../../../release/compatibility.md) for supported device and firmware versions.
