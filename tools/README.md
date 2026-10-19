# Developer tools

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Environment inventory, capability queries and container-side SDK/package tools.
The tools use Python 3.10+. Inventory and package inspection need no installed SDK;
the explicit SDK integration command additionally executes Bazel, a compiler and SDK tests.

## Environment inventory

```bash
python3 tools/check_environment.py --profile host
python3 tools/check_environment.py --profile container --robot-type foot_quadruped
```

Host inventory checks for Bash, Git and Docker on PATH; Bazel is required only in the
container profile, which checks Bash, Git and Bazel without requiring Docker.
For real Docker readiness checks and the container handoff, follow the [container guide](../docker/README.md).
Python's version is checked against the local tooling baseline of 3.10;
this does not check SDK native dependencies or the device Python ABI.
Other tools are only located, never executed. The expected Bazel version comes from
`.bazelversion`, not an observed version of the installed binary.

Output is JSON. Exit 0 means the local inventory completed without missing required tools or
a blocked robot type; 1 means those local requirements need attention; 2 means invalid input
or invalid checkout/catalog data. Argument-parser errors are written to stderr.
The `sdk_status` is separate from local inventory success and repository integration.
It is `blocked_integration` when catalog SDK integration is `pending`, and `not_verified`
when integration is `integrated`: this inventory never imports the SDK or checks its ABI.
Use `python3 tools/vbot_catalog.py --summary` for SDK metadata and separate Recipe/Blueprint counts generated
from the catalog, rather than treating an inventory exit code as application readiness.

The helper never invokes Docker, installs packages, pulls images, connects over SSH, or calls
robot APIs. It reports untested areas explicitly. An omitted robot type stays unselected;
unknown types fail, and planned types do not inherit software support from shared hardware.

## Capability query

```bash
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability device.agent.content
```

See [catalog format and decisions](../catalog/README.md).
Exit 0 means a successful query, including queries returning blocked capabilities; exit 2
means an invalid query or catalog. The tool does not execute catalog entries.

Both helpers resolve the reference checkout from their physical file location, so they can
be invoked by absolute path from another application directory.
Use `--root` only to explicitly select a different complete VBOT Lab checkout.

## Device shell inventory

In the device's configured `vbot` shell, with the standalone file already available:

```bash
python3 tools/check_device_environment.py
```

This helper checks the effective account, readable public setup files, selected environment
variables, and `aorta` / `ros2` / `timeout` lookup. It rejects a shadowed Aorta executable.
It does not print ambient values or session file contents, run tools, edit files, or contact
interfaces. Exit 0 means shell checks passed; 1 means attention is required; 2 means invalid
arguments. It does not prove device identity, ROS type loading, live reception, or persistence.
Unlike the checkout-based tools above, it needs no catalog or SDK and accepts no `--root`.
See [device setup](../docs/getting-started/device-environment.md) for manual checks, transfer
scope, `.bashrc` configuration, and separate bounded live checks.

## Download pinned SDK inputs

Run inside the development container, from the checkout root:

```bash
python3 tools/fetch_sdk.py --output artifacts/edu-sdk-2026.10.14
```

The default `python` profile downloads seven files: four Linux ARM64/base wheels,
`EDU_SDK_MANIFEST.json`, `SHA256SUMS` and the FlatBuffers license. Versions and hashes come
from [release.json](../catalog/release.json), not a mutable "latest" lookup. Use
`--platform linux_x86_64` for local native SDK tests, or `--profile all` for all SDK assets
including C++ and Schema archives. Verified existing files are reused; invalid files are
reported without overwriting them. Downloads require network; no SDK installation,
build or SSH occurs. Prepared assets can be supplied separately for disconnected use.

## Package a Python Recipe

Build and preview the selected Recipe in the container first. Then package it separately:

```bash
python3 tools/package_python.py --recipe subscribe-state \
  --assets-dir artifacts/edu-sdk-2026.10.14 --output artifacts/first-state &&
python3 tools/package_python.py --verify artifacts/first-state
```

Packaging is container-only, defaults to `linux_aarch64`, requires a new output directory,
and performs no build, install, network or device operation. `--platform linux_x86_64`
creates a **local preview** package, not a robot-deployable artifact. The selected Recipe
must be in the capability catalog. The tool checks the four base wheels' pinned hashes,
platform tags, distribution metadata, dependency closure and bundled license material.

Output contains only the selected source entry/shared modules, LICENSE/NOTICE, four wheels,
SDK manifest, FlatBuffers license, pinned `requirements.txt`, `PACKAGE_MANIFEST.json` and
`SHA256SUMS`. The manifest records source hashes, target and dependency/license inventory;
no venv, session configuration, keys or whole-checkout copy is included.
NumPy/PyAV payload-saving/decoding options are outside this base profile; see
[Python deployment](../docs/development/python-deployment.md) before using them.

`--verify` only reads an existing package and may run on the host or CI. It rejects changed,
missing or extra files and mismatched SDK pairing. It validates the platform recorded in
`PACKAGE_MANIFEST.json` against the packaged wheels, not the host architecture.
Do not combine `--verify` with `--recipe`, `--assets-dir`, `--output` or an explicit
`--platform`; these combinations return argument error 2. Both `PACKAGE_MANIFEST.json`
and `SHA256SUMS` must be regular files inside the package, not symlinks or special files.
These hashes check integrity, not a
publisher signature or live device compatibility. Transfer/install/run are separate,
explicit steps in [Quickstart](../docs/getting-started/README.md); packaging never deploys.

## SDK integration without a robot

In the development container, select a new work directory for each run:

```bash
python3 tools/sdk_ci.py --download \
  --assets-dir artifacts/sdk-ci-assets --work-dir artifacts/sdk-ci-work
```

With `--download`, retrieve/reuse the full pinned Release. Omit it only when all assets
are already present. After hash checks, the tool installs into a clean native venv, checks
imports/dependencies, builds all Python and C++ Recipe targets, and runs real generated-type
and C++ SDK tests with transport mocked. It also installs a freshly generated package into
a second clean venv, runs its offline preview, verifies an ARM64 package, and runs synthetic
packaging tests. In every clean SDK venv it clears `AORTA_CORE_FFI_LIB`, explicitly calls
`aorta.load_library()`, verifies that the loaded library is bundled in that venv's wheel,
and checks its ABI against the release configuration without creating a Node.
On Linux x86_64 it additionally cross-builds all eleven base C++ Recipes
and the C++ SDK test binary with the ARM64 SDK. `cpp_artifacts.py` reads their ELF headers,
interpreter, GLIBC requirements and recursive `DT_NEEDED` dependencies against target SDK/
compiler libraries. It also checks actual ARM64 compile actions for `fastbuild`, `opt`
and `dbg`. Documented deployment command chains are tested with fake commands, including
checksum/build/transfer failures, empty output directories, missing libraries, and
account/architecture/Python-version mismatches before device writes.
It never executes these ARM64 files. Existing work directories are never overwritten.

Release retrieval and initial Bazel dependency resolution need network; wheel installation
is offline. This is no-device CI, not a fully disconnected build from scratch. It does not
create an Aorta Node, connect over SSH, or establish robot runtime results. Native tests
and ARM64 artifact inspection are separate; neither establishes ARM64 execution on a robot.
Follow [offline Bazel](../docs/development/offline-build.md) for packaged build dependencies.

On first use, Bazelisk may download the Bazel version pinned by .bazelversion. SDK CI allows
180 seconds for that preparation; use --bazel-prepare-timeout SECONDS (30–600) when needed.
The compiler-only version probe retains its 20-second limit. A preparation failure reports
JSON on stderr with stage=bazel_prepare, a distinct error_code, and a safe reason such as
dns, tls, proxy, http, integrity or network. Raw download output/URLs are not printed.
bazel_prepare_timeout is a tool-preparation problem, not evidence of SDK incompatibility.

The three commands above return 0 on completion, 1 on failed inputs/context/operation, and
2 on invalid CLI arguments. `sdk_ci.py` additionally needs Bazel 7.6.1, a native C++17
compiler, the image's ARM64 GCC/G++ 11/binutils and `tar` with Zstandard support. Failed partial output is left for inspection;
choose a new output/work directory after correcting the cause.

## Independent applications and diagnostics

SDK integration builds both health-monitor implementations, runs the Python/C++ model and real-type
serialization tests, and cross-builds/inspects the C++ ARM64 program. C++ preview/parity tests never open a Node.
Application workspace/package and diagnostic regression tests run in the container-only packaging group.

In the development container, use `create_app.py --name my-monitor --output /tmp/my-monitor`
to create a Python workspace from the [health-monitor Blueprint](../blueprints/health-monitor/README.md).
Use `create_app.py --language cpp --name my-cpp-monitor --output /tmp/my-cpp-monitor` for C++.
See [application templates](../templates/README.md) for the files and language boundaries.
The C++ project includes relocated source/helpers, local SDK rules and ARM64 toolchains;
follow its README for native tests, cross-builds and binary/library deployment.
SDK integration builds/tests this independent workspace too, without device access.
The generated Python workspace is also built/tested, packaged with real SDK wheels, verified
and installed in a fresh venv for native-runtime/ABI checks and offline preview/simulation.
Its ARM64 package is verified separately without executing it.
`package_app.py --project /tmp/my-monitor --assets-dir artifacts/edu-sdk-2026.10.14 --output /tmp/my-monitor-package`
packages the Python project's explicit APP.json runtime inventory and four pinned SDK wheels without building or deploying.
`package_app.py --verify /tmp/my-monitor-package` is read-only and may run on the host/CI.
Output directories must be new; extra dependencies need a separately prepared application-specific workflow.
The packager creates APP.json and reserves its deployment controls, wheelhouse/ and licenses/;
source_files must not overlap them. See the generated [Python workspace guide](../templates/python-app/README.md)
for the exact paths. Both packaging and verification reject conflicts before extraction.

`diagnose.py --level inventory` is local and read-only. SDK execution stays in the container;
device and single-stream sampling are explicit opt-in levels in the device vbot shell.
The sdk/sample levels require Python SDK. C++ uses the guide's separate SDK-input,
device-library and selected-route CLI checks, without a Python venv or wheel install.
See [layered diagnostics](../docs/development/diagnostics.md) for commands, status semantics and sharing boundaries.

Use [vbot-app-dev](../skills/vbot-app-dev/SKILL.md) for application work or
[vbot-diagnose](../skills/vbot-diagnose/SKILL.md) for scoped failure investigation.

## Validation and future tools

Follow [execution locations](../docs/development/README.md). Repository-only checks can run
on the host or CI runner; Bazel, Recipe previews, simulated application tests, dependency
preparation and packaging must run in the matching development container, including CI.

```bash
python3 tools/run_checks.py --scope repository
```

Inside the inspected development container, from the checkout root:

```bash
python3 tools/container_context.py &&
python3 tools/in_container.py -- bazel build //recipes/subscribe-state:main &&
python3 tools/run_checks.py --scope recipes &&
python3 tools/run_checks.py --scope packaging
```

`container_context.py` is read-only and returns 0 for an eligible declared container context,
1 otherwise, and 2 for invalid arguments. Runtime markers and `VBOT_DEV_CONTAINER=1` are both
required. The guard does not verify image identity or workspace mounts; inspect them first
using the container guide. `in_container.py` checks that context before executing the explicit
command, preserves arguments and working directory, and propagates its exit status. It does
not enter/create containers or connect to robots automatically.

`run_checks.py --scope ... --list` only lists [check groups](../catalog/checks.json).
Without `--list`, it returns 0 only if every selected check passes; 1 indicates a failed
check, invalid group metadata or missing context, and 2 indicates invalid CLI arguments.
Neither `CI=true` nor `--profile container` exempts container-only checks.

`check_release.py` compares [release configuration](../catalog/release.md) against the
checkout's component versions and optionally checks already-downloaded manifests and
asset hashes. It is offline, read-only and does not publish or certify a release.

For packaged Bazel dependencies, see [offline builds](../docs/development/offline-build.md).
`prepare_bazel_offline.py` explicitly prepares a bundle inside a connected development container;
`bazel_offline.py` verifies it and runs Bazel without repository downloads.
Unlike inventory helpers, these two tools execute build tools and write build outputs.

Schema generation, user-program deployment, and device log-collection tools remain planned.
See [Skills](../skills/README.md) for workflows and [tests](../tests/README.md) for evidence scope.
