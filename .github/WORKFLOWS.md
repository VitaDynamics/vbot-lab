# CI and repository collaboration

<p align="center">English | <a href="WORKFLOWS.zh-CN.md">中文</a></p>

For PRs and pushes to `main` or `pre_release/**`, the workflow separates repository inspection
from application execution. `repository-checks` runs read-only content and mocked tool checks
on a GitHub-hosted runner. `recipe-checks` runs SDK-free previews and simulated application
flows inside the development container selected by `docker/compose.yaml`.
`sdk-integration` uses that same pinned container configuration for real SDK integration,
fresh-venv installation, all Python/C++ Recipe builds, SDK serialization tests and package
completeness checks. It verifies the assets pinned in `catalog/release.json` before use.
Each fresh SDK venv explicitly loads the wheel-bundled native library, verifies its origin and
release ABI, and clear `AORTA_CORE_FFI_LIB`; successful imports alone are not sufficient.
It also cross-builds the base C++ Recipes for ARM64 and inspects target ELF/dependencies;
actual ARM64 compile actions are checked for `fastbuild`, `opt` and `dbg`.
ARM64 programs are not executed on the AMD64 runner/container.
Checkout, image/SDK retrieval and initial Bazel dependency resolution need network access;
pip installation then uses only the verified local wheels. This is a no-device integration
job, not a fully network-disconnected build from scratch. No check contacts robots, creates
an Aorta Node, or launches model sessions.

The existing required `repository-layout` job aggregates all three jobs and fails if any
fails, is skipped or is cancelled. [checks.json](../catalog/checks.json) is the shared check
inventory used locally and in CI. See [execution locations](../docs/development/README.md).

See [SDK checks](../tools/README.md#sdk-integration-without-a-robot) for the same local command.
Synthetic package tests run in that container job; repository inspection remains host-safe.
It also builds the Python/C++ health-monitor Blueprint, runs native model/decoder/CLI tests,
cross-builds the C++ program/tests for ARM64 without execution, and tests independent
Python/C++ workspace generation, Python packaging and diagnostic workflows. A generated C++
workspace is built/tested independently with native SDK previews and ARM64 artifact checks.
A generated Python workspace is also built/tested, packaged with real pinned SDK wheels,
verified, installed in a fresh venv and exercised through offline preview/simulation.
Its ARM64 package is verified without executing ARM64 code.

## Before committing or opening a PR

From the repository root on the host or CI runner:

```bash
python3 tools/run_checks.py --scope repository
```

Inside the inspected development container, at the same checkout root:

```bash
python3 tools/run_checks.py --scope recipes
```

The host may invoke the second command through the selected container. Do not run Recipe
tests, Bazel or packaging on the runner/host directly, even when they need no SDK or network.
If the container is unavailable, report those checks as not run instead of falling back.

Record the results and any relevant build or device checks with the change, following
[Contributing](../CONTRIBUTING.md). Use the bug-report or documentation template
when opening an issue; general usage questions belong in [Community & Support](../docs/community/README.md).

The [release-configuration checks](../catalog/release.md) compare local component
pairing and test mismatch handling. They do not download attachments or publish a Release.

## Iteration updates

Use the `pre_release/V<major>.<minor>.<patch>.X` branch for the selected version family.
Maintainers may commit and push directly after running the applicable checks;
iteration updates do not require a PR. Topic PRs are optional when review is wanted.
Retain protection against force pushes and deletion. CI runs on iteration-branch pushes,
but does not require opening a PR or obtaining a pre-push CI result for each new commit.

## Formal release review and merge

1. Open a PR to `main` only when formal release is explicitly requested.
2. Obtain approval from another maintainer listed in [CODEOWNERS](CODEOWNERS).
   New reviewable commits dismiss earlier approvals; someone other than the latest
   pusher must approve the latest changes.
3. Resolve review discussions and ensure the GitHub Actions check `repository-layout`
   passes against the current target branch. Update the topic branch if the base advances.
4. Use **Squash and merge**. Protect `main` against direct pushes, force pushes and
   deletion, with no administrator bypass.

## Version iterations and formal promotion

| Reference | Role |
| --- | --- |
| `main` | Latest formal release; do not merge work-in-progress version updates |
| `pre_release/V1.6.0.X` | Long-lived iteration branch for the `V1.6.0` family; the final `X` stays literal |
| `V1.6.0.12` | Source tag for robot application `V1.6.0-12`; select the exact source tag recorded in the release configuration |
| `edu-sdk-*` | SDK attachment Release tags; independent of source tags and robot application versions |

The `V1.6.0` branch is not shared by all future versions. A new family such as
`V1.6.1` uses its own `pre_release/V1.6.1.X` branch.

1. Create a new family branch from a known baseline; keep existing iteration content
   when adopting this workflow. Subsequent changes may be committed directly to that
   family branch, without a required PR.
2. Update [release configuration](../catalog/release.md), component pairing and both
   languages. Run the offline checks and applicable SDK/build/device checks before
   recording the checked iteration commit under a new source tag.
3. An iteration tag is not a formal release approval. Continue changes on the selected
   iteration branch; do not open a promotion PR during ordinary iteration work.
4. Only when formal release is explicitly requested, select the exact checked snapshot,
   complete the release configuration, and open a promotion PR to `main`. Do not merge unrelated
   changes or move the existing iteration tag. Record any newly required changes under
   a new tag instead.
5. After release approval and maintainer review, update VBOT Lab's `main` through its
   PR process and publish the approved source version and SDK attachments as needed.
   This workflow does not publish releases automatically. Never reset or force-push `main`.

Tags matching `V*` and `edu-sdk-*` can be created but cannot be moved or deleted.
Publish corrections under a new tag; do not retarget an existing version.
Creating a source tag does not create a GitHub Release: this workflow has no tag or
Release-publishing trigger. SDK download assets remain separate from source tags.

## Automation safety

The workflow uses a read-only token, GitHub-hosted runners and a full-commit-SHA-pinned
checkout action with persisted Git credentials disabled. Repository defaults also use
read-only tokens, disallow Actions from approving PRs and require actions to be pinned
to full commit SHAs. Changes to CI should retain these boundaries and must not expose
secrets to untrusted PR code or operate a robot.

Dependabot alerts cover dependencies GitHub can discover; they are not a complete audit
of Bazel dependencies, downloaded SDK archives or native libraries. Check those separately
when updating the [SDK pairing](../docs/compatibility.md). Send vulnerability reports
privately as described in [Security](../SECURITY.md).
