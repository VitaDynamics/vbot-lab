# Application templates

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

These files support the application generator; they are not robot interfaces or standalone
examples. The generator combines template documentation/build files with the runnable
[health-monitor Blueprint](../blueprints/health-monitor/README.md). Business source remains
in that Blueprint so fixes are shared by the reference application and newly generated projects.
Generated projects start from this application; this is not a generator for arbitrary robot behaviors.

From the VBOT Lab root, inside the development container, choose a new output directory:

```bash
python3 tools/create_app.py --language python --name my-python-app --output /tmp/my-python-app
python3 tools/create_app.py --language cpp --name my-cpp-app --output /tmp/my-cpp-app
```

Each command is independent. Omitting --language keeps the Python default.
Names use 1–48 lowercase letters, digits or hyphens, start with a letter, and end with a
letter or digit. For example, my-app is valid; my-app- is rejected before any files are created.
Existing output directories are never overwritten. Generation does not download/install SDKs,
run Bazel, deploy, or contact a robot. Read the generated README before building.

| Template | Generated project |
| --- | --- |
| [Python](python-app/README.md) | Python source/tests, Bazel entry points, pinned requirements and APP.json; package with package_app.py |
| [C++](cpp-app/README.md) | C++ source/tests, local SDK rule, copied shared helpers, ARM64 toolchain, native/ARM64 build steps and binary deployment |

README and AGENTS documents are copied into the new project for its users and Coding Agents.
Files ending in .template become the project's build/test files, not device runtime inputs.
C++ workspaces contain their build logic and source dependencies, but not SDK binaries or headers;
point them at verified native/ARM64 release artifacts outside the source tree.

Both languages receive the same gitignore.template as .gitignore. It excludes local environment
files, device-session configurations, credential dictionaries, private-key filenames and packaged
artifacts; .env.example remains visible for sanitized configuration examples. Keep credentials
outside the project. Ignore rules do not scan for secrets or protect files already tracked by Git.
