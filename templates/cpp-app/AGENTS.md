# C++ application instructions

<p align="center">English | <a href="AGENTS.zh-CN.md">中文</a></p>

Read README.md and APP.json first. Keep business state in health_monitor/model.h,
FlatBuffer access in decoder.h, and subscriptions/reporting in main.cc.
Build, test, preview and package inside the matching VBOT development container.
Reuse the existing container. Use the native SDK for native tests/previews and the ARM64
SDK with --config=arm64 for device builds; never execute cross-built targets on AMD64.
The workspace is independent: do not add source includes, Bazel labels or local_repository
references back to the VBOT Lab checkout. SDK artifacts stay outside source control.
Copy borrowed message bytes before deferring them and validate FlatBuffers before access.
Default execution is a preview. Tests never create a Node or contact devices.
Device execution requires the selected robot, vbot shell, matching versions and --execute.
Only observe the documented three streams. Control or recording needs separate user intent.
Keep missing input distinct from unsupported interfaces; preserve bounded waits and cleanup.
Update build/package inventories for added runtime files/libraries. Package and deploy separately.
Preserve user files and Agent configuration; do not configure autostart or change ACLs to test.
