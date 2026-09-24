# Developer tools

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Local environment checks and capability queries.
The current tools use Python 3.10+ and the standard library, with no SDK dependency.

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
The `sdk_status` is separate: it remains `blocked_integration` for this checkout,
even when local inventory exits 0.

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

## Validation and future tools

For packaged Bazel dependencies, see [offline builds](../docs/development/offline-build.md).
`prepare_bazel_offline.py` explicitly prepares a bundle on a connected machine;
`bazel_offline.py` verifies it and runs Bazel without repository downloads.
Unlike inventory helpers, these two tools execute build tools and write build outputs.

```bash
python3 tests/check_repository.py
python3 tests/test_agent_workspace.py
bazel test //tests:repository_layout_test //tests:agent_workspace_test
```

Schema generation, user-program deployment, and device log-collection tools remain planned.
See [Skills](../skills/README.md) for workflows and [tests](../tests/README.md) for evidence scope.
