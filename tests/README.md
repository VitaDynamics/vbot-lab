# Tests

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Run from the checkout root with Python 3.10+ and Bash:

```bash
python3 tests/check_repository.py
python3 tests/check_schemas.py
python3 tests/test_agent_workspace.py
python3 tests/test_recipes.py
python3 tests/test_family_recipes.py
bazel build //:repository_files //recipes/...
bazel test //tests:repository_layout_test //tests:agent_workspace_test //tests:recipe_test
```

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

Every tracked text file is checked for private network addresses, workstation paths, device
host names and private repository names, and no session configuration, credential dictionary
or key file may be tracked. `tests/check_schemas.py` checks that `schemas/ros2/` holds exactly
the definitions the public routes in `routes.json` use, plus the types they reference and the
constant holders that document their values, and that `MANIFEST.json` matches the tree.

## Agent workspace

The offline suite checks:

- Catalog format, identifiers, references, known/unknown robot types, and release decisions.
- Separation of documented device contracts, planned integrations, and local tooling.
- Host versus container prerequisites, missing tools, Python compatibility, and CLI exit codes.
- No external-command or network calls during inventory.
- Device-shell account, public-file access, environment mismatch, executable shadowing, redacted output, and standalone CLI exit codes; all tested without a robot.
- Shared Skill content through Codex / Claude Code aliases and Claude's shared-instruction import.
- Relative directory-symlink metadata in the source checkout.
- An individual Skill linked from an external application, including a reference checkout path with spaces.

Bazel materializes its runfiles, so the source-directory symlink metadata test is skipped there;
the aliased Skill contents are still tested. The direct Python suite and GitHub Actions check
the actual source symlinks. CI runs the repository, workspace and SDK-free Recipe Python suites, not device tests.

## Manual workflow checks

[Fresh-session scenarios](agent-scenarios/README.md) cover actual Skill discovery and task
selection in Codex / Claude Code. They are not run by the deterministic test suite.
The offline suite does not launch harness sessions, SDK applications, containers, or device programs.

Ordinary external PRs must not trigger real-device tests.

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

All are manual targets. Ordinary CI neither downloads the SDK nor operates devices;
run these explicitly and do not report unexecuted tests as passing.
