# Shared back mounting and arm adapter plate for robot dogs

<p align="center">English | <a href="back-mounting.zh-CN.md">中文</a></p>

Use this reference to check the back mounting holes and design an adapter for a
robot arm or another accessory. The mounting dimensions, adapter plate and
illustrated fastener configuration are shared by four-legged robot dogs
(`foot_quadruped`) and wheeled quadruped robot dogs (`wheel_quadruped`).
This specification does not apply to bipedal robots (`foot_humanoid`).

Both robot-dog types use this single reference. Shared mechanical hardware does
not change the [EDU software release scope](../../robots/README.md).

These are mechanical drawings and a component CAD model, not a robot URDF,
an arm-control interface, or a statement of supported payload.

## Drawings and CAD files

| File | Use |
| --- | --- |
| [Back mounting holes (PDF)](assets/back-mounting/back-mounting-holes.pdf) | Locate the robot-side threaded holes and read the back-cover reference dimensions |
| [Arm adapter plate (PDF)](assets/back-mounting/arm-adapter-plate.pdf) | Read plate dimensions, hole patterns, tolerances, material and finish |
| [Arm adapter plate (STEP)](assets/back-mounting/arm-adapter-plate.step) | Import the plate into CAD; the model uses millimeters |
| [Installation illustration (JPEG)](assets/back-mounting/arm-installation.jpeg) | Identify the plate and the two fastener sets |

Download the STEP file and open it in a compatible CAD application; it is not a
URDF upload for [Vbot Viewer](../../guides/vbot-viewer.md). For robot-description
file availability, see [robot models](../../../assets/robots/README.md).
The engineering drawings retain their original annotations; the tables below
explain the key dimensions and Chinese installation callouts in English.

## Dimensions at a glance

All dimensions below are in **mm**. Use the PDF's dimension lines to identify the
corresponding features; do not infer dimensions by measuring a screenshot.

| Feature | Drawing value |
| --- | --- |
| Robot-side mounting holes | 4 × M4, thread depth 6 |
| Robot-side hole center spacing | 115.5 × 89 |
| Other back-cover reference spans | 152 × 109, as indicated in the back mounting drawing; not a guaranteed usable accessory footprint |
| Adapter plate overall dimensions | 125.5 × 99; thickness 7 |
| Plate-to-robot clearance holes | 4 × Ø4.50 through; center spacing (115.5 ±0.2) × (89 ±0.2) |
| Arm-to-plate threaded holes | 4 × M5-6H through; Ø4.20 through pilot holes; center spacing (70 ±0.2) × (70 ±0.2) |
| Plate material and finish | 6061 aluminum alloy, clear anodized finish |

For the remaining cutouts, offsets, unspecified-dimension tolerances and geometric
requirements, use the plate PDF. Its notes refer to the 3D model for dimensions
not annotated in the drawing. Do not replace the dimensioned drawing with the
summary above when preparing a part for manufacture.

## Installation illustration and parts

![Arm base on the back adapter plate, with plate and fastener callouts](assets/back-mounting/arm-installation.jpeg)

| Drawing callout | Part | Quantity | Connection shown |
| --- | --- | --- | --- |
| 2 — 铝合金转接板 | Aluminum adapter plate | 1 | Between the robot's back plate and the arm base |
| 3 — 圆柱头螺钉 M4×12 | Cylindrical-head screw M4×12 | 4 | Adapter plate to robot |
| 4 — 圆柱头螺钉 M5×10 | Cylindrical-head screw M5×10 | 4 | Arm base to adapter plate |

In the plate drawing, **完全贯穿** means **through**, **未注尺寸公差** means
**tolerances for dimensions without an individual tolerance**, and **本色阳极氧化**
means **clear anodized finish**.

The fasteners above describe the illustrated assembly. If plate thickness, arm-base
thickness or washers change, check the required screw length and actual thread
engagement again; do not bottom out screws in the robot's blind holes.

## Before fitting an accessory

- Keep the robot powered off and stably supported while fitting hardware. Check
  hole spacing, thread depth and clearance against the actual mounting surface.
- Keep connectors, cooling openings and the robot's moving parts unobstructed;
  check the accessory and cable routing throughout their intended range of motion.
- These files do not specify payload, allowable moment, center-of-mass limits,
  tightening torque, or an approved arm model. Confirm those requirements for the
  intended robot/accessory combination before operating it.
- Mechanical fit does not provide arm power, communication, drivers or motion
  coordination. Do not infer those capabilities from the illustration or STEP file.

For fit questions, use [Community & Support](../../community/README.md) and include
the relevant drawing, hardware model and the dimension or interface in question.
