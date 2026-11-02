# Release configuration

<p align="center">English | <a href="release.zh-CN.md">中文</a></p>

[release.json](release.json) records one component combination for a VBOT Lab source
snapshot. It is a local, machine-readable pairing configuration, not a release
announcement or an installer. Component versions remain independent.

The configuration uses the selected application, SDK, Schema and development image
references. It records the intended source branch and tag; this does not create Git
refs or announce a release. The development branch is `release/V1.6.0`, the formal
source tag is `Rel/V1.6.0`, the robot application is
`V1.6.0-15`, and the SDK Release is `edu-sdk-2026.10.31`. The image digest is pinned.

## Fields

| Field | Meaning and allowed values |
| --- | --- |
| `format_version` | Integer `1`; unknown fields and duplicate JSON keys are rejected |
| `workspace.branch` | Development branch for the selected release: `release/V1.6.0`. The format also accepts `main` and long-lived iteration branches such as `pre_release/V1.6.1.X`; `X` is literal |
| `workspace.tag` | Formal snapshot `Rel/V1.6.0`, matching the `release/V1.6.0` branch family. Iteration branches instead use a matching numeric iteration tag; robot application and SDK versions remain separate |
| `robots` | Current released robot types from `catalog/robots/`; each records its exact `application_version`, not a minimum version |
| `sdk.repository`, `sdk.release_tag` | GitHub download repository (`owner/name`) and exact EDU SDK bundle Release tag |
| `sdk.aorta_version` | Aorta SDK package version, aligned with the Python and C++ SDK |
| `sdk.python` | Minimum Python version (`major.minor`), exact versions of the four wheel packages, and available wheel platform tags |
| `sdk.cpp` | Exact SDK version, positive integer ABI, distribution identifier and available architectures; keep ABI aligned with the Bazel native-library import |
| `sdk.assets` | Attachment inventory: exact filenames and lowercase 64-character SHA-256 values, including checksum/manifest/license attachments; no credentials or signed download URLs |
| `schema` | Schema version, pack revision, archive name/checksum and ROS 2 bridge pairing from the generated `schemas/MANIFEST.json`; the pack revision may differ from the Schema version |
| `development.bazel_version` | Exact `.bazelversion` value |
| `development.image` | Tagged Compose default image reference and a `sha256:<64 lowercase hex characters>` digest; `null` means the digest has not been recorded |

Package versions use three numeric components, optionally followed by a revision such
as `-v4`. Application versions use `V<major>.<minor>.<patch>`, optionally with a numeric build suffix such as `-10`. Unknown compatibility
must not be filled by copying another component's version.

All source-owned content—guides, interface references, Recipes, Blueprints, Skills,
tools, catalogs, hardware/model assets and build configuration—belongs to the source
snapshot. These directories do not each need a separate release version. Downloaded
SDK binaries have their own Release references and hashes.

## Source branches and tags

Develop V1.6.0 applications on `release/V1.6.0`, not on a detached tag or an iteration
branch. `Rel/V1.6.0` identifies its formal source snapshot, paired with robot application
`V1.6.0-15`. The earlier `V1.6.0.15` tag remains an iteration snapshot, not the development
entry point. `main` contains the latest formal release.

At formal promotion, merge the reviewed changes to `main` through its PR process, then
create `release/V1.6.0` and `Rel/V1.6.0` from that same merged commit. This keeps the three
references aligned without rewriting history. Selecting a branch or creating a tag does
not automatically create a GitHub Release.

For a new version family, prepare iterations on its own
`pre_release/V<major>.<minor>.<patch>.X` branch; iteration updates do not require a PR.
The V1.6.0 iteration is complete. Do not reuse its branch for another family.
Existing tags identify immutable snapshots. See the
[collaboration workflow](../.github/WORKFLOWS.md) for review and promotion steps.

The configuration does not replace [capability metadata](README.md), robot profiles,
generated Schema metadata or SDK installation instructions. The checker compares
these sources and reports inconsistent combinations rather than rewriting them.

## Check the combination

From the checkout root, using Python 3.10+:

```bash
python3 tools/check_release.py
python3 tests/test_release.py
```

The tool uses only the standard library and local files. It does not contact GitHub,
Docker or a robot, install anything, create tags or publish Releases. Output is JSON:
exit `0` means locally consistent (possibly with `pending` fields), `1` means strict
completion was requested but fields remain unfilled, and `2` means invalid input or
a mismatch. Argument errors also return `2`, with argparse output on stderr.

To require the source tag and image digest to be filled:

```bash
python3 tools/check_release.py --require-complete
```

Completion checks syntax and recorded
pairing; it does not prove tag existence, download visibility, image identity or device
compatibility. A missing image digest or source tag intentionally fails this strict check.

After downloading SDK assets through the [SDK guide](../packages/aorta/python/README.md),
optionally compare the published manifest and hash the local attachments:

```bash
SDK_RELEASE_TAG=$(python3 -c 'import json; print(json.load(open("catalog/release.json"))["sdk"]["release_tag"])')
python3 tools/check_release.py \
  --sdk-manifest "artifacts/${SDK_RELEASE_TAG}/EDU_SDK_MANIFEST.json" \
  --sdk-assets-dir "artifacts/${SDK_RELEASE_TAG}"
```

The directory must contain **every** attachment listed in `sdk.assets`; a single-platform
SDK installation is not the full inventory. Extra unrelated files are ignored; missing,
changed or symlinked attachments are rejected. SDK manifest comparison alone checks
metadata, not binary contents.

## Keep updates aligned

| Changed component | Review together |
| --- | --- |
| Source snapshot / robot support | Source branch/tag, robot profiles, `docs/compatibility.md`, `AGENTS.md`, capability scope and changelog; do not move existing tags |
| SDK / native ABI | Public Release inventory and checksums, `catalog/capabilities.json`, Python/C++ installation guides, `recipes/common.py` version guard and `packages/aorta/cpp/repositories.bzl` native import |
| Schema / routes | Generated `schemas/` and `schemas/MANIFEST.json`, SDK generated bindings, public interface guides and capability references; regenerate rather than hand-edit generated files |
| Guides / Recipes / Skills / tools | Both languages, catalogs and agent routing, setup/deployment instructions and tests; modified live examples need device checks before publication as required by [Contributing](../CONTRIBUTING.md) |
| Development environment | Compose image reference and digest, `.devcontainer/`, `.bazelversion`, Bazel module/lockfile and documented tool prerequisites |
| Hardware / models | Asset manifests, robot-type applicability, documentation and licensing notices |
| Test expectations | Offline tests and any version-specific expectations; checks do not automatically migrate examples or dependencies |

Record each component's dependency version and artifacts independently. The configuration
is suitable for inspection by local tools, but no automatic publication is configured.
