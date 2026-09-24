# Vbot Viewer: explore and edit robot models

<p align="center">English | <a href="vbot-viewer.zh-CN.md">中文</a></p>

[Open Vbot Viewer](https://vbot-viewer.vitarobot.cc/?model=VbotBaboEDU) to explore
the four-legged EDU model, inspect joints and links, edit URDF, and export model files.
It runs in a browser; viewing a model does not require SSH, Docker, the SDK, or a robot connection.

Use Viewer for **robot descriptions and model poses**. Use [Foxglove](foxglove.md)
for **live robot messages**. Moving a Viewer joint slider does not command a physical
robot, and exporting a pose does not create a deployable locomotion trajectory.

![Vbot Viewer with model tools on the left, a 3D viewport in the center, and joints and links on the right](assets/vbot-viewer/overview.jpg)

The overview uses the English interface. Controls available for a particular model
may differ; switch between **EN / 中文** in the header.

## 1. Open a model

1. Open the link above in a modern browser such as Chrome or Edge.
2. If prompted, sign in using an available account method. New users can select
   **Register** and follow the account/activation instructions shown on the page.
   Use **Forgot password** to recover access; do not share account or device-binding details in public posts.
3. Select **VbotBaboEDU** in **Model**. The link's `?model=VbotBaboEDU` selects this
   shared model; it is not a device address or a live robot connection.
4. Select the desired URDF in **Files**. Confirm the model and filename before inspecting or editing.

The current repository's model location is
[assets/robots/foot_quadruped](../../assets/robots/foot_quadruped/README.md).
It bundles a snapshot of the VbotBaboEDU URDF and meshes. The online model can change
independently; check `model.json` for the local entry file.
Other models visible on the website do not establish EDU interface support for other robot types.

## 2. Inspect structure and model poses

| Task | Control | What to check |
| --- | --- | --- |
| Look around | Left-drag to orbit, right-drag to pan, scroll to zoom | Use the direction cube to inspect a face in orthographic view |
| Find a component | Hover a link or select it in **Links** | Link name, parent-relative position, mass, center of mass and inertia |
| Keep information visible | Double-click a link to pin its popup | Close individual popups or use **Clear popups** |
| Understand joint axes | **Axis** buttons and joint sliders | Joint name, rotation/translation axis and declared limits |
| Inspect contact geometry | **Collisions** | Collision shapes versus the visual mesh; these are different model elements |
| Inspect declared inertia | **Inertia**, when available | Equivalent inertia boxes and their placement; investigate suspicious values in the URDF |
| Compare variants | Split the viewport, then select a model/file per pane | Side panels act on the focused pane |

Rotational joints use radians or degrees as selected by **rad / deg**; prismatic
joints use meters. Displayed limits and physical properties come from the model,
not measurements of the connected robot. A plausible-looking pose is not proof that
the physical robot can safely reach it.

**Pose** buttons load model keyframes. **Copy angles** exports joint values; preserve
joint ordering, names and units when using them in another application. **+ Keyframe**
on a shared model saves a server-side named pose visible to other users. Use it only
when you intend to make that shared change; it is not the same as saving a local URDF edit.

## 3. Edit and save a local variant

1. Choose the correct model/file and focus its viewport.
2. Enable **Edit URDF** for structured link/joint fields, or **Edit Source** for XML
   with a 3D preview. Inspect origins, axes, limits, inertial fields and collision geometry as needed.
3. Correct XML errors before saving. **Ctrl+S** saves; the first save creates a named
   local variant. **Ctrl+Shift+S** creates another copy. Select the saved variant in **Files**.
4. Use **Download** to export work you want to keep. Select the intended URDF variant;
   the model's meshes accompany the archive.

Local variants are stored in that browser and do not overwrite the shared model.
Clearing site data removes them, and they do not automatically follow you to another
computer/browser. Save a downloaded copy before clearing data. The website's shared
model may be updated independently of any repository snapshot.

For your own model, **Upload** or drag a folder containing exactly one `.urdf` plus
its referenced meshes. Uploading a browser-local model is different from publishing
it to the shared model library. Browser-local `.xacro` uploads are not supported.

| Model source | Browse / edit / download | Server-side URDF checks and MJCF conversion | Shared keyframes |
| --- | --- | --- | --- |
| Shared model, including a local edited variant based on it | Supported | Supported where the tools are available | Available for the shared model; affects other users |
| Your uploaded browser-local model | Supported | Not supported | Not supported |

Local storage does not mean every operation is offline: URDF checks, repair and MJCF
conversion use server-side processing. Only submit model content you are authorized to process there.

## 4. Check and export a model

For a shared model or a local variant based on one:

1. Run **Tools → URDF validation** for the focused model. Review errors and warnings,
   then use the validation overlay to locate the affected links.
2. Read the report: **ERROR** identifies a definite structural/physical inconsistency,
   **WARNING** requires investigation, and **INFO** may describe a skipped check.
   Checks use the URDF's zero pose, not the pose currently set by the sliders.
3. Export the PDF report or copy the AI repair prompt if useful. Give your coding
   assistant the relevant model files and report, review its proposed changes, and
   check the edited model again. Do not automatically apply model edits to a robot.
4. Download the selected URDF variant and meshes. For MuJoCo input, use
   **URDF → MJCF**, choose full geometry or collision-only output, and download the result.

**Repair URDF** changes model descriptions, including joint-axis conventions and mesh
collisions, and produces a new local variant. If an axis direction flips, angle signs
and associated keyframes/controller values need corresponding review. Keep the original
model; do not assume existing control parameters remain interchangeable.

Model checks can detect inconsistencies but do not establish real hardware accuracy,
controller compatibility, or safe motion. MJCF conversion is an export step, not a
complete simulation or robot deployment workflow.

## 5. Get help

| Symptom | First check |
| --- | --- |
| Cannot sign in or activate an account | Follow the page's activation/recovery instructions; never post passwords, codes or device SNs |
| A local upload has missing meshes | Include the referenced files and preserve resolvable paths in the model folder |
| Saved edits are missing | Use the same browser and selected variant; check your exported backups |
| Validation or conversion is unavailable | Check the model-source table above; a browser-local upload does not support those server-side tools |
| A control changes the wrong view | Focus the intended pane before using the side panels |
| The model reloads | The shared model may have been updated; retain your exported local work |

Still stuck, or have an improvement idea? Visit [Vbot 超能社区](https://forum.vbot.cn/).
For Viewer issues, include the model/file name, browser version, operation steps and a
sanitized screenshot or short error excerpt. Follow [Community & Support](../community/README.md)
for the right category and a copyable report template. Share your solution in the same
topic when resolved so other developers can benefit.
