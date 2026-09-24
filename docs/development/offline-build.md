# Offline example builds

<p align="center">English | <a href="offline-build.zh-CN.md">中文</a></p>

Use Bazel 7.6.1 and a matching dependency bundle to build without fetching build
rules from a registry. The bundle contains the public rules, registry metadata,
and upstream license files needed by the Python/C++ Recipes. It does not contain
the Aorta SDK, compiler, Python interpreter, or FFmpeg.

## Prepare the build machine

Obtain the release-matched bundle from your development-environment provider, or
prepare it on a connected machine using the procedure below. No prebuilt bundle
is attached to the current SDK pre-release yet; the preparation tool does not
publish one. Do not assume an existing development image contains it.

Prepare these items before disconnecting:

- Bazel 7.6.1 and a native C++17 compiler with the matching Linux system headers/libraries.
- The dependency bundle for this checkout's `MODULE.bazel` and `MODULE.bazel.lock`.
- The matching [C++ SDK and Schema pack](../../packages/aorta/cpp/README.md).
- For Python execution, the matching [SDK wheels](../../packages/aorta/python/README.md)
  and FlatBuffers wheel, installed in a dedicated venv.
- For optional image decoding, compatible `av==16.1.0` and `numpy==2.2.6` wheels for Python, or FFmpeg
  development/runtime libraries for C++. Bazel does not install these.

SDK artifacts must first be downloaded from GitHub Releases with network access.
The `edu-sdk-2026.9.24` release attaches the `flatbuffers` 25.12.19 wheel next to the SDK
wheels; [Python deployment](python-deployment.md) also shows how to obtain it from PyPI.
Prepare any optional dependencies as well. The commands below assume that complete,
verified wheelhouse is already available.

Keep wheel files together in a wheelhouse; then install without package-index access:

```bash
python -m pip install --no-index --find-links artifacts/wheelhouse \
  aorta-sdk==2026.9.23 aorta-msgs==2026.9.23 vbot-edu-msgs==2026.9.24 flatbuffers==25.12.19
```

## Build from the bundle

Extract a verified bundle into `artifacts/offline/bazel/` so that it contains
`manifest.json` and `vendor/`. Keep the C++ SDK environment variables configured
as described in its guide. From the checkout root:

```bash
python3 tools/bazel_offline.py --output-user-root "$PWD/artifacts/bazel-output" \
  build //recipes/... //recipes/device-info:main_cpp //recipes/subscribe-state:main_cpp \
  //recipes/service-call:main_cpp //recipes/camera:main_cpp //recipes/audio:main_cpp \
  //recipes/locomotion:main_cpp //recipes/rcp-task:main_cpp
python3 tools/bazel_offline.py --output-user-root "$PWD/artifacts/bazel-output" \
  run //recipes/subscribe-state:main_cpp
```

Use this wrapper instead of bare `bazel` when offline. It checks the bundle's file
hashes, checkout module/lock hashes, and Bazel version before starting; ignores
ambient Bazel configuration; disables WORKSPACE fallback and repository downloads;
and uses a dedicated output/cache directory. A missing bundle fails before Bazel
starts. The preview above does not contact a robot. Live execution still requires
each Recipe's device environment and explicit operation flags.

The wrapper is not a network sandbox for arbitrary build rules or applications.
It does not disable network access requested by `bazel run` programs. New targets
or build configurations may require a new bundle. Never use a workstation's SDK
libraries or generated CPU configuration on an incompatible robot architecture.

## Prepare a bundle

On a connected machine with the SDK paths and optional decoder build dependencies
prepared, run:

```bash
python3 tools/prepare_bazel_offline.py --output artifacts/offline/bazel
tar -czf artifacts/bazel-offline.tar.gz -C artifacts/offline/bazel .
sha256sum artifacts/bazel-offline.tar.gz
```

The destination must not already exist. Preparation uses public upstream
dependencies through Bazel's [vendor mode](https://bazel.build/external/vendor),
preserves their license files, and records a checksummed snapshot. Local host
platform detection is deliberately regenerated on the consuming machine.
Transfer the archive and its trusted checksum with the matching SDK artifacts.
Keep generated dependency trees in the release bundle, outside Git.

For a development image, include this bundle, wheelhouse, SDK, native build tools,
and optional decoder dependencies during image creation. Check a fresh output/cache
directory without external network access before distributing the image. A warm
cache build is not a substitute for verifying the packaged inputs.
