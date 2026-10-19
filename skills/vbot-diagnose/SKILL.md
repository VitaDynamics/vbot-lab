---
name: vbot-diagnose
description: Diagnose an existing VBOT application's environment, SDK import/linkage or missing telemetry using explicit read-only levels and sanitized summaries. Use for failures and troubleshooting, not automatic repair, deployment, motion or capture.
---

# Diagnose a VBOT application

<p align="center">English | <a href="SKILL.zh-CN.md">中文</a></p>

Resolve this Skill's physical directory to its VBOT Lab checkout, even when discovered from
another application. Confirm tools/diagnose.py exists there; do not execute a same-named file
from the application's working directory. If the checkout is incomplete, request its location.

## Narrow the failure

Identify the observed command/error, execution location, Python/C++ choice, known version pairing
and selected route/device from available evidence. Ask only for missing details needed for
the next check. Start from the [symptom index](../../docs/troubleshooting/README.md) and
[layered diagnostics](../../docs/development/diagnostics.md), not a scan of every interface.
Review relevant application source/configuration without displaying credentials or session files.

## Select one explicit diagnostic level

- Local tools only: run tools/diagnose.py --level inventory; it does not contact a device,
  install tools, check Docker, import an SDK or prove that an application is ready.
- Python SDK: use the application's selected venv in the development container with
  --level sdk. Keep metadata versions, native-library origin and ABI separate from robot access.
- C++ SDK/linkage: follow the C++ section of the diagnostic guide, with matching native/ARM64
  artifacts and compiler targets. Missing Python wheels are not a C++ failure; do not install
  them to repair C++ linkage or run host ldd on ARM64 binaries.
- Device shell: only when device inspection is requested, use the selected connection and
  the documented vbot shell. Transfer of diagnose.py is a separate write; request that scope
  if it is not already covered. --level device --allow-device-check checks shell prerequisites,
  not interface support or the robot application version.
- One sample: only when sampling is requested, use --level sample --allow-device-check with
  one of state/battery/system and a bounded --timeout. Python sampling needs its application
  venv. The C++ diagnostic path uses a bounded device Aorta CLI sample instead.

Levels do not authorize the next level. Follow [execution locations](../../docs/development/README.md)
and reuse the selected development container for SDK/build work. If SSH is unreachable,
stop and ask for connection or the actual address; do not scan/switch devices. Authentication
and host-key failures are separate from reachability; do not bypass verification or embed passwords.

## Interpret and hand off

Separate confirmed_missing, mismatch, not_verified and waiting_data_timeout. A timeout is
not proof of unsupported firmware, ACL rejection, a stopped producer or hardware failure.
sample_received confirms bytes only, not decoding or freshness. A local subscription is not
proof of a remote producer. Preserve sampling/cleanup failures and report each reached stage.

Give the observed result, remaining uncertainty and smallest relevant next check.
Do not restart services, change permissions/quotas/modes, reinstall dependencies, publish controls
or collect audio/video as an automatic repair. Diagnose-only requests do not authorize fixes.
Review the minimal JSON summary before sharing; omit raw exceptions, host/session/credential data.
Offer a reviewed [community report](../../docs/community/README.md), never automatic posting.
