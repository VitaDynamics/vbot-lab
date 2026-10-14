# CI and repository collaboration

<p align="center">English | <a href="WORKFLOWS.zh-CN.md">中文</a></p>

The current workflow runs repository-content and offline agent-workspace checks on
GitHub-hosted runners for PRs and pushes to `main` or `pre_release/**`.
GitHub Actions checks out the code; the check script itself makes no network requests
and performs no device operations.

It validates bilingual documentation, relative Codex / Claude Code Skill links, capability
catalog decisions, local environment-tool behavior, and SDK-free Recipe previews and safety guards.
It does not launch model sessions or open Aorta sessions.

Dependency builds and SDK tests are not yet included in this workflow.

## Before committing or opening a PR

Run the same offline checks from the repository root:

```bash
python3 tests/check_repository.py
python3 tests/check_schemas.py
python3 tests/test_agent_workspace.py
python3 tests/test_recipes.py
python3 tests/test_family_recipes.py
python3 tests/test_offline_build.py
python3 tests/test_release.py
```

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
| `V1.6.0.10` | Iteration source tag for robot application `V1.6.0-10`; later iterations receive new numeric suffixes |
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
