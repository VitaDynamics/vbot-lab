# CI and repository collaboration

<p align="center">English | <a href="WORKFLOWS.zh-CN.md">中文</a></p>

The current workflow runs repository-content and offline agent-workspace checks on GitHub-hosted runners.
GitHub Actions checks out the code; the check script itself makes no network requests
and performs no device operations.

It validates bilingual documentation, relative Codex / Claude Code Skill links, capability
catalog decisions, local environment-tool behavior, and SDK-free Recipe previews and safety guards.
It does not launch model sessions or open Aorta sessions.

Dependency builds and SDK tests are not yet included in this workflow.

## Before opening a PR

Run the same offline checks from the repository root:

```bash
python3 tests/check_repository.py
python3 tests/check_schemas.py
python3 tests/test_agent_workspace.py
python3 tests/test_recipes.py
python3 tests/test_family_recipes.py
python3 tests/test_offline_build.py
```

Include the results and any relevant build or device checks in the PR, following
[Contributing](../CONTRIBUTING.md). Use the bug-report or documentation template
when opening an issue; general usage questions belong in [Community & Support](../docs/community/README.md).

## Review and merge

1. Make changes on a topic branch and open a PR targeting `main`.
2. Obtain approval from another maintainer listed in [CODEOWNERS](CODEOWNERS).
   New reviewable commits dismiss earlier approvals; someone other than the latest
   pusher must approve the latest changes.
3. Resolve review discussions and ensure the GitHub Actions check `repository-layout`
   passes against the current `main`. Update the topic branch if the base advances.
4. Use **Squash and merge**. Direct pushes, force pushes and deletion of `main` are blocked.
   Administrators have no protection bypass configured.

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
