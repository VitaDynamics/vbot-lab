# Python application workspace

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

A standalone Bazel workspace based on the read-only health monitor. Keep application changes
here rather than editing your VBOT Lab reference checkout. Requires Python 3.10+, Bazel 7.6.1
and the VBOT development container. The supported robot application is V1.6.0-12 (foot_quadruped);
SDK Release edu-sdk-2026.10.14 supplies the pinned requirements.

## Build and test — development container

From this generated application's root:

```bash
bazel build //:main &&
bazel test //:model_test &&
bazel run //:main &&
bazel run //:main -- --simulate
```

The default command prints a plan; simulation uses synthetic data and never imports the SDK.
`health_monitor/model.py` holds business rules, `runtime.py` owns device subscriptions,
and `main.py` owns CLI configuration, reporting and shutdown. Edit config.json or pass
`--config /path/to/config.json`. Freshness is measured using local monotonic receive time,
recorded in the callback and preserved through the queue, not dequeue time or comparison of
different stream clocks. Delayed processing cannot refresh old samples. SDK-reported drops
and application queue overflow stop the program. Missing/stale data is not a hardware-fault diagnosis.
wire.py reads the pinned SDK BFBS metadata to validate the three message structures before decoding.
Malformed input increments invalid without refreshing data; legal zero/default fields remain valid.
Validation is bounded to 1 MiB per sample, 64 nested levels and 65,536 objects, and does not authenticate
the producer. No extra dependency is needed; previews and simulation do not load these schemas.

Python failures write JSON to stderr with status=error, stage, error_code and next_step,
without raw exceptions or configuration contents. config_not_found and invalid_config belong
to stage=config and stop before SDK/device access; sdk_not_installed, sdk_version_mismatch
and sdk_load_failed belong to stage=sdk. Environment and subscription failures have their own
stages; unexpected failures use runtime/unexpected_error. Follow the supplied next_step and
the [error guide](https://github.com/VitaDynamics/vbot-lab/blob/main/docs/troubleshooting/README.md#application-errors).

## Package — development container

Use the absolute path to your matching VBOT Lab checkout and prepared SDK assets.
The example assumes /workspace/vbot-lab and an application under /workspace/my-app:

```bash
python3 /workspace/vbot-lab/tools/package_app.py --project /workspace/my-app \
  --assets-dir /workspace/vbot-lab/artifacts/edu-sdk-2026.10.14 \
  --output /workspace/my-app-package &&
python3 /workspace/vbot-lab/tools/package_app.py --verify /workspace/my-app-package
```

Replace these paths with the actual mounted locations. Output must be a new directory outside
the application. APP.json explicitly lists runtime files; update it when adding modules/configuration.
Only listed Python/JSON files and LICENSE/NOTICE are packaged, along with four pinned wheels and checksums.
No venv, session configuration or whole repository is copied. Additional third-party dependencies
are not automatically resolved; the base packager rejects requirements outside the pinned SDK pairing.
The packager generates the deployment APP.json automatically; do not add it to source_files.
Top-level APP.json, EDU_SDK_MANIFEST.json, SHA256SUMS, requirements.txt and application.tar.gz,
plus the complete wheelhouse/ and licenses/ namespaces, are reserved for the deployment package.
Packaging and verification reject application files at or beneath those paths. Put custom metadata
in app-info.json or inside health_monitor/; a nested health_monitor/APP.json does not conflict.
Verify the complete, unextracted package before transfer. Extraction adds application files without
overwriting package files, so the original SHA256SUMS remains valid afterward.

## Deploy and run — device vbot shell

First transfer the complete verified package to a new user application directory using your
existing SSH connection. No repository, compiler or Bazel is required on the robot.
After login, replace APP_DIR with that directory:

```bash
APP_DIR=/userdata/vbot/apps/my-app-REPLACE &&
cd "$APP_DIR" &&
sha256sum -c SHA256SUMS &&
tar -xzf application.tar.gz &&
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
python3 -m venv .venv &&
.venv/bin/python -m pip install --no-index --find-links wheelhouse -r requirements.txt &&
.venv/bin/python -m pip check &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
.venv/bin/python -m health_monitor.main --config config.json --execute --duration 10
```

Expected: JSON Lines identify each stream as waiting_data, receiving or stale. The final
all_streams_receiving field is true only when all three streams are fresh. A live run exits 0
only when all three streams are fresh at the end; successful preview/simulation also exits 0.
Exit 1 means missing/stale data at the end, or a configuration/input/runtime failure; it does
not necessarily mean a program fault. Exit 2 means invalid CLI arguments, such as an unknown
option, an invalid duration or conflicting modes. Ctrl+C exits 130.
The low_battery flag is advisory and does not trigger any control operation. A timeout
does not establish that an interface is unsupported. Nothing starts automatically at boot.
For a new login, re-enter APP_DIR, clear the two Python overrides, set the same environment,
and rerun the last command without reinstalling. Subscribers and the Node close on exit.

Start from [VBOT Lab](https://github.com/VitaDynamics/vbot-lab) for connection, environment
and interface guides. Use the [Python diagnostic path](https://github.com/VitaDynamics/vbot-lab/blob/main/docs/development/diagnostics.md)
for environment or missing-data issues. Share reproducible issues in [Vbot 超能社区](https://forum.vbot.cn/),
after reviewing diagnostic summaries; do not share credentials or session configuration.
