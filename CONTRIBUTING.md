# Contributing

<p align="center">English | <a href="CONTRIBUTING.zh-CN.md">中文</a></p>

Before submitting a change, describe the developer problem it solves,
the affected features, validation, and compatibility impact.

See [CI and repository collaboration](.github/WORKFLOWS.md) for the current automated checks.

For usage questions, application discussions and feature ideas, start with
[Community & Support](docs/community/README.md). Use repository issues/PRs for concrete
code or documentation changes, and link an existing forum discussion when relevant.

- Use Bazel for Python and C++ recipes and reference applications; keep SDK APIs, Schema, code, documentation, and Skills consistent.
- Put Aorta SDK integration under `packages/aorta/python/` and `packages/aorta/cpp/`, single-task reference programs under `recipes/`, and complete reference applications under `blueprints/`. Document actual availability; outlines and planned Blueprints must not appear runnable.
- Maintain one Skill source under `skills/`, exposed through `.agents/skills/` and `.claude/skills/` symlinks. Keep `CLAUDE.md` as a thin import of the shared `AGENTS.md`; do not maintain divergent harness instructions. Skill discovery uses English `SKILL.md`; its `.zh-CN.md` is the paired translation.
- Keep `AGENTS.md` short and task-oriented. Record capability scope and references in `catalog/`, retain structural facts in Schema, and explain behavior in interface docs. Check catalog changes with the offline tool tests; unknown versions and routes must not become implied support.
- Maintain every document in English and Simplified Chinese. Default filenames use English; translations use `.zh-CN.md`. Update both in the same PR and retain language navigation and same-language document links.
- Write user guides as complete, correct usage workflows: prerequisites, commands, responses, completion conditions, and recovery. Keep test reports separate from usage instructions.
- Follow the [robot-type documentation structure](docs/robots/README.md): reuse shared chapters and hardware specifications, isolate type-specific differences, and update the release scope and compatibility matrix without implying support for unreleased types.
- Keep the existing shared wired connection and sensor specification for `foot_quadruped` and `wheel_quadruped`; do not duplicate them or apply them to `foot_humanoid`. Current EDU release scope remains `foot_quadruped` until separately released and documented.
- Include the dependencies needed to build Schema changes and keep generated Python bindings consistent.
- Include reproducible steps and relevant test results; follow the [security guidance](SECURITY.md) when sharing reports.
- Run `python3 tests/check_repository.py`, `python3 tests/test_agent_workspace.py`, and the relevant Bazel checks. Distinguish offline tests from actual harness-session and device behavior.
- Distinguish read-only device checks from control operations; never operate robots automatically in ordinary CI.
- Before releasing a new or modified live example, run every published language implementation and documented execution path on a supported robot using the documented account, SDK pairing, setup and deployment steps. Compilation, previews and offline tests alone do not meet this release gate. Keep verification evidence in the review record, not in public usage guides; unresolved or untested paths must not be released as runnable examples.

## Maintainers and review

The repository administrators are the maintenance team. They triage issues, review
contributions and coordinate compatibility changes. [CODEOWNERS](.github/CODEOWNERS)
lists the reviewers for all repository paths; update it when administrator membership changes.
Review routing does not grant repository permissions or replace configured merge requirements.

Report security concerns privately using [Security](SECURITY.md), not a public issue or PR.

## Licensing contributions

Unless explicitly stated otherwise, contributions intentionally submitted for inclusion
are provided under [Apache-2.0](LICENSE), as described in Section 5. Submit only material
you have the right to contribute, and retain applicable third-party license and attribution
notices, including those in [NOTICE](NOTICE).
