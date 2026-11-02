# Tests

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

From the checkout root with Python 3.10+ and Bash, run repository-only checks on the host
or CI runner:

```bash
python3 tools/run_checks.py --scope repository
```

Inside the matching development container, from the checkout root:

```bash
python3 tools/container_context.py
python3 tools/run_checks.py --scope recipes
python3 tools/run_checks.py --scope packaging
bazel build //:repository_files //recipes/...
bazel test //tests:repository_layout_test //tests:agent_workspace_test //tests:recipe_test //tests:release_configuration_test
```

Follow [execution locations](../docs/development/README.md). All Bazel invocations, SDK tests,
Recipe previews and application tests run in the container, including CI. Listing a group
with `--list` is read-only. The shared groups live in [checks.json](../catalog/checks.json);
the runner fails before running Recipe checks outside an eligible development context.

## Independent applications

Skill tests cover shared discovery and preserving external project instructions/other Skills;
fresh harness behavior remains a manual check.

`test_applications.py` runs in the container-only packaging group. It covers standalone
workspace creation, non-overwrite behavior, explicit source inventories, reproducible
dual-architecture packages with synthetic wheels, preview/simulation isolation, subscription
cleanup/overflow and diagnostic opt-in/timeout semantics. It also runs the health-monitor
model tests for empty input, stale streams, ordering, invalid values and recovery.
`//blueprints/health-monitor:model_test` and `//tests:applications_test` are Bazel entries.
No test connects to a robot. SDK integration CI includes the packaging group.
Generated Python CLI subprocess tests check exit codes 0/1/2/130 for previews, simulation,
argument/configuration errors, missing/stale streams and interruption. Stream/interrupt cases
use fake transport and clocks; SDK imports are blocked in every subprocess.
Regression cases preserve callback timestamps across delayed consumption and reject SDK drops
before/after dequeue, including an empty wait. C++ serialization tests also preserve callback
time when consuming queued messages and reject invalid data without refreshing the valid sample.
Name-boundary tests reject trailing hyphens before generation and apply the same rules to
Python package manifests. Diagnostic tests distinguish SDK import, Node creation, subscription,
sample arrival and cleanup failures using fake SDKs only.
Real Git checks exercise both generated projects' shared ignore rules, including environment
variants, session files, credential dictionaries, keys and the visible .env.example exception.
The real-SDK suite validates full/default messages and corrupt root offsets, vtables, fields,
nested headers, strings and table vectors. Malformed data cannot make the Python monitor succeed
or refresh a previous valid sample; C++ tests also reject the same all-zero input.

The parallel [C++ health monitor](../blueprints/health-monitor/cpp/README.md) has explicit
`model_cpp_test`, `sdk_cpp_test` and `//tests:health_monitor_cpp_test` targets. They cover
SDK-free state transitions, real FlatBuffer decoding, CLI/configuration failures and
Python/C++ state-summary parity without creating a Node. SDK integration runs these native
tests, then cross-builds the program and C++ tests for ARM64 without executing them.
The generator supports Python and C++ with independent build files. C++ generation tests check
relocated includes, toolchain/metadata completeness and explicit Python-packager rejection.
SDK integration also builds/tests a generated C++ workspace, runs its native preview/simulation
and cross-builds/inspects its ARM64 program/tests, without contacting a device.
It also builds/tests a generated Python workspace, packages real SDK wheels, verifies the bundle,
installs in a fresh venv, checks the wheel-native ABI and runs offline preview/simulation.
The independent application's ARM64 package is verified, not executed.
The installed independent Python package also decodes legitimate default messages and rejects
all-zero buffers using its bundled wire.py and the installed SDK metadata, without opening a Node.
Package tests reject reserved deployment paths during packaging and verification, even if archive
and manifest checksums were rebuilt. Both architecture packages are extracted with tar, then checked
for unchanged bundle files and valid original SHA256SUMS; app-owned nested metadata remains allowed.
The real-SDK integration also checks the generated Python package's SHA256SUMS before and after extraction.

## Repository and documentation

The layout suite checks bilingual pairs, frontmatter-aware language navigation, same-language
links, matching code examples, Agent-first navigation, Recipe task entries, and retired paths.
It also preserves robot-type boundaries, shared sensor values and connection photos/settings,
documented SSH commands, device Agent API routes, MCP JSON/handshake order, and Bash syntax.
Device environment examples are syntax-checked; a stubbed `source` checks setup order and
export values without loading device files. Aorta / ROS 2 identifiers match across translations.
Usage guides are checked for report-only sections and sampled-accuracy statistics.
Viewer/community navigation and issue-chooser links are checked locally. The model check
verifies the bundled `foot_quadruped` URDF entry, mesh inventory and mesh references;
the checks do not contact the Viewer or post to the forum.
The shared back-mounting reference checks attachment integrity, navigation from both
robot-dog types, and bilingual dimension/fastener parity without a PDF or CAD runtime dependency.

Documented SSH / HTTP commands are inspected as text or syntax, never executed against devices.
Skill discovery aliases are excluded from duplicate document traversal; canonical `skills/`
documents are checked once.

Every tracked text file is checked for sensitive network addresses, workstation paths, device
host names and non-distributable identifiers, and no session configuration, credential dictionary
or key file may be tracked. `tests/check_schemas.py` checks that `schemas/ros2/` holds exactly
the definitions the public routes in `routes.json` use, plus the types they reference and the
constant holders that document their values, and that `MANIFEST.json` matches the tree.

## Agent workspace

The offline suite checks:

- Catalog format, identifiers, references, known/unknown robot types, and release decisions.
- Python/C++ Blueprint source/target entries, owning Bazel packages, and separate Recipe/Blueprint summaries.
- Separation of documented device contracts, planned integrations, and local tooling.
- Host versus container prerequisites, missing tools, Python compatibility, and CLI exit codes.
- No external-command or network calls during inventory.
- Device-shell account, public-file access, environment mismatch, executable shadowing, redacted output, and standalone CLI exit codes; all tested without a robot.
- Shared Skill content through Codex / Claude Code aliases and Claude's shared-instruction import.
- Relative directory-symlink metadata in the source checkout.
- An individual Skill linked from an external application, including a reference checkout path with spaces.

Bazel materializes its runfiles, so the source-directory symlink metadata test is skipped there;
the aliased Skill contents are still tested. The direct Python suite and GitHub Actions check
the actual source symlinks. CI runs repository/workspace checks on the runner; SDK-free
Recipe suites and the separate pinned-SDK integration job run in the development container,
never on devices. See [CI](../.github/WORKFLOWS.md).

`test_execution_policy.py` checks group separation, container guard rejection before subprocess
or output creation, generated SDK/Recipe summaries and the combined CI gate. All command
execution in those guard tests is mocked; they never run a Recipe, Bazel or Docker.

## Manual workflow checks

[Fresh-session scenarios](agent-scenarios/README.md) cover actual Skill discovery and task
selection in Codex / Claude Code. They are not run by the deterministic test suite.
The repository suite does not launch harness sessions, SDK applications, containers, or device programs.

Ordinary external PRs must not trigger real-device tests.

## Release configuration

`test_release.py` checks the [release configuration](../catalog/release.md) against
robot profiles, capability metadata, Recipe version guards, the C++ ABI import,
generated Schema metadata, SDK guides, Compose and Bazel. It also covers unfilled
fields, iteration branch/tag pairing, invalid inputs, published-manifest comparisons
and file-hash failures using local synthetic fixtures. It does not download assets,
pull images, verify live devices or publish anything; a consistent draft is allowed
in ordinary CI. Use `--require-complete` explicitly to reject unfilled release fields.

## Recipes and release SDK

`test_recipes.py` needs no SDK and checks offline previews, argument limits, device-environment guards,
explicit voice/motion confirmation, queue overflow, deadlines, correlation and resource cleanup.
`test_recipe_sdk.py` is explicit and requires the matching wheels. It checks actual generated types,
service headers, RCP union/dependency serialization and simulated transport flows for motion reports,
RCP success/cancel/timeout cleanup and audio/video parsing. Creating a real Node is forbidden in the tests.

After installation through the [SDK guide](../packages/aorta/python/README.md), run:

```bash
bazel test --test_env=PATH="$PWD/.venv/bin:$PATH" //tests:recipe_sdk_test
```

The target is tagged manual, so ordinary `bazel test //...` does not require wheel downloads.
Builds and offline checks do not establish live device results.

## Explicit C++ tests

Offline bundle integrity, checkout matching, path checks, and missing-bundle
failures are tested without downloading dependencies or starting Bazel:

```bash
python3 tests/test_offline_build.py
```

Use the [offline build guide](../docs/development/offline-build.md) to run Bazel
targets with packaged dependencies. These unit checks alone do not prove that a
bundle contains everything needed for a fresh build.

Set artifact directories through the [C++ SDK guide](../packages/aorta/cpp/README.md), then run:

```bash
bazel test //tests:recipe_cpp_test //tests:recipe_cpp_sdk_test
```

The first target runs previews, help and invalid-argument checks for all eleven C++ binaries,
including every stream selector in the four new read-only families.
The second checks actual generated DAG unions/dependencies, service headers, FlatBuffer
validation, deadlines, interruption and exclusive output without creating a Node.
The optional decoder test additionally requires FFmpeg development libraries and a libx265
encoder; it generates only local synthetic frames:

```bash
bazel test //tests:recipe_cpp_decoder_test
```

All SDK-dependent targets are manual and run in the development container. The separate
CI SDK job explicitly selects the three base SDK targets; the optional decoder remains a
separate check. Neither job operates devices. Do not report unexecuted tests as passing.

## Clean SDK integration and Python packages

Inside the development container:

```bash
python3 tools/sdk_ci.py --download \
  --assets-dir artifacts/sdk-ci-assets --work-dir artifacts/sdk-ci-work
```

This checks the pinned Release hashes, clean native SDK installation/imports, all Recipe
builds, `recipe_sdk_test`, `recipe_cpp_test`, `recipe_cpp_sdk_test`, and a second clean
installation/offline preview from a generated package. It also verifies an ARM64 package
without running ARM64 binaries on x86_64. Every work directory must be new.
Each clean SDK venv explicitly loads the wheel-bundled native runtime and checks its origin
and release ABI, with `AORTA_CORE_FFI_LIB` cleared; imports alone do not cover lazy loading.
On Linux x86_64 it also builds the eleven base C++ Recipes plus the SDK test binary for
ARM64 and inspects ELF architecture, interpreter, GLIBC requirements and target-library
dependencies. These ARM64 test binaries are built, not executed. Native SDK tests still run.
Both health-monitor implementations are also built; their model, serialization and C++ CLI
tests run natively, and the C++ program/model/serialization tests are cross-built for ARM64.
The SDK check also inspects real compile actions for ARM64 `fastbuild`, `opt` and `dbg`.
Downloads and initial Bazel resolution need network; pip uses local wheels. No real Node
or device connection is created. See [tool scope](../tools/README.md#sdk-integration-without-a-robot).

`test_python_packaging.py` uses synthetic wheels for deterministic package integrity,
metadata, architecture/dependency/license failures, tampering, output preservation and
container-guard tests. It also checks verification/packaging argument conflicts,
default/explicit target selection, and rejection of missing, symlinked or non-regular
control files before any content read, plus unlisted special files. Read-only verification
covers both package architectures. It runs under `--scope packaging` or the manual
`//tests:python_packaging_test` target, only in the container. Those unit tests do not
execute the SDK; mocked native-runtime probes also cover load failure, wrong ABI,
external/missing libraries, symlink escape and override removal in both installation modes.
The clean installation above covers the actual pinned SDK.

`test_deployment_commands.py` runs the bilingual Quickstart, Python deployment, Python SDK
installation, C++, both application templates, the C++ Blueprint and offline-bundle preparation/tool command chains against fake commands.
It injects failure at each tool invocation and checks that later commands do not run;
it also covers empty directories, missing libraries, venv activation failure and
preservation of the interactive shell/variables. Recipe-switching checks validate
empty, required and multiple preview arguments against the real offline CLI with
SDK/device access blocked. SSH prechecks
are evaluated locally against fake account/architecture/version observations, ensuring a
mismatch stops before directory creation or transfer; C++ needs no Python runtime. It never
builds, installs or connects to a device. Run it under `--scope packaging` or the manual
`//tests:deployment_commands_test` target in the development container. SDK CI includes
both packaging suites.

Mocked checks in `test_execution_policy.py` cover wrong/truncated ELF inputs, wrong
interpreters, newer GLIBC requirements and unresolved target libraries without invoking
binutils. Offline-wrapper tests check ARM64 target selection and reject cross `run`/`test`;
native tests explicitly inherit only the checked container declaration while still rejecting
host execution and ignoring external Bazel configuration.
