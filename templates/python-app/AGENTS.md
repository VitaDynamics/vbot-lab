# Application instructions

<p align="center">English | <a href="AGENTS.zh-CN.md">中文</a></p>

This is an independent user application. Read README.md and APP.json before changing it.
Keep business rules in health_monitor/model.py and device subscription/decoding in runtime.py.
Build, test, simulate and package only inside the VBOT development container; reuse an existing
matching container. Inventory-only checks may run on the host or CI.
Default execution is a preview. Device execution requires the selected robot, the vbot shell,
matching SDK/application versions and explicit --execute. Do not add device contact to tests.
The provided application only observes telemetry; adding control or capture requires separate
user intent and the relevant interface safety conditions. Keep missing data distinct from an
unsupported interface. Preserve the user's files and Agent configuration. Do not deploy,
configure autostart, install keys or publish feedback merely to test business logic.
Update APP.json when changing runtime source files; packaging and deployment are separate.
