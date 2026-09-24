"""Prepare a portable Bazel 7.6.1 dependency bundle; run on a connected build machine."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from urllib.request import urlopen
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["//recipes/...", "//tests:repository_layout_test", "//tests:agent_workspace_test", "//tests:offline_build_test",
           "//tests:recipe_test", "//tests:family_recipe_test", "//tests:recipe_sdk_test", "//tests:recipe_cpp_test",
           "//tests:recipe_cpp_sdk_test", "//tests:recipe_cpp_decoder_test"] + [
    f"//recipes/{name}:main_cpp" for name in
    ("device-info", "subscribe-state", "service-call", "camera", "audio", "locomotion", "rcp-task",
     "sensors", "perception", "system-peripherals", "slam")
] + ["//recipes/camera:main_cpp_decode"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new bundle directory")
    parser.add_argument("--bazel", default="bazel")
    args = parser.parse_args()
    version = subprocess.check_output([args.bazel, "--version"], text=True).strip()
    if version != "bazel 7.6.1":
        parser.error("this bundle requires Bazel 7.6.1")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    vendor = output / "vendor"
    vendor.mkdir()
    # This repository is generated locally without downloading. Never ship the
    # producing machine's CPU constraints to another architecture.
    (vendor / "VENDOR.bazel").write_text('ignore("@@platforms~host_platform~host_platform")\n')
    subprocess.run([args.bazel, "--ignore_all_rc_files", "vendor", f"--vendor_dir={vendor}",
                    "--noenable_workspace", "--lockfile_mode=error", *TARGETS], cwd=ROOT, check=True)
    # Bazel creates an external-cache convenience link; it is not portable input.
    external_link = vendor / "bazel-external"
    if external_link.is_symlink():
        external_link.unlink()
    # Freeze this checksummed release snapshot, not machine-specific repository
    # marker digests. Consumers regenerate only the ignored local host platform.
    repositories = sorted(path.name for path in vendor.iterdir()
                          if path.is_dir() and not path.name.startswith("_"))
    with (vendor / "VENDOR.bazel").open("a") as stream:
        for name in repositories:
            stream.write(f'pin("@@{name}")\n')
    # Pinned snapshots do not use cache markers; Bazel may delete them on use.
    for marker in vendor.glob("@*.marker"):
        marker.unlink()
    # Bazel 7 may move its private _registries directory between vendor roots.
    # Ship only lockfile-selected, content-addressed metadata independently.
    registry_dir = vendor / "_registries"
    if registry_dir.exists():
        shutil.rmtree(registry_dir)
    cache = Path(subprocess.check_output(
        [args.bazel, "--ignore_all_rc_files", "info", "repository_cache"], cwd=ROOT, text=True).strip())
    lock = json.loads((ROOT / "MODULE.bazel.lock").read_text())
    for url, sha in lock["registryFileHashes"].items():
        if not url.startswith("https://bcr.bazel.build/") or len(sha) != 64:
            raise ValueError(f"unexpected registry input: {url}")
        cached = cache / "sha256" / sha / "file"
        data = cached.read_bytes() if cached.is_file() else urlopen(url, timeout=30).read()
        if hashlib.sha256(data).hexdigest() != sha:
            raise ValueError(f"registry checksum mismatch: {url}")
        parsed = urlsplit(url)
        target = vendor / "_registries" / parsed.netloc / parsed.path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for path in vendor.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"unexpected vendor symlink: {path.relative_to(output)}")
    files = {str(path.relative_to(output)): digest(path)
             for path in sorted(output.rglob("*")) if path.is_file()}
    manifest = {"bazel": "7.6.1", "module_sha256": digest(ROOT / "MODULE.bazel"),
                "lock_sha256": digest(ROOT / "MODULE.bazel.lock"), "targets": TARGETS, "files": files}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared {len(files)} files in {output}; SDKs and compiler/runtime dependencies are separate.")


if __name__ == "__main__":
    main()
