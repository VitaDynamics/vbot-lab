"""Run Bazel with a verified, portable dependency bundle; never prepare/download it implicitly."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle):
    manifest = json.loads((bundle / "manifest.json").read_text())
    if manifest["bazel"] != "7.6.1":
        raise ValueError("unsupported bundle Bazel version")
    actual = {str(path.relative_to(bundle)) for path in bundle.rglob("*")
              if path.is_file() or path.is_symlink()} - {"manifest.json"}
    if "vendor/VENDOR.bazel" not in manifest["files"] or actual != set(manifest["files"]):
        raise ValueError("bundle file inventory changed; obtain a complete, matching bundle")
    for name, key in (("MODULE.bazel", "module_sha256"), ("MODULE.bazel.lock", "lock_sha256")):
        if digest(ROOT / name) != manifest[key]:
            raise ValueError(f"bundle does not match {name}; obtain a matching bundle")
    for name, expected in manifest["files"].items():
        path = bundle / name
        if not path.resolve().is_relative_to(bundle) or path.is_symlink() or digest(path) != expected:
            raise ValueError(f"bundle file failed verification: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "artifacts/offline/bazel")
    parser.add_argument("--bazel", default="bazel")
    parser.add_argument("--output-user-root", type=Path, required=True,
                        help="dedicated Bazel output/cache directory")
    parser.add_argument("command", choices=("build", "test", "run"))
    args, extra = parser.parse_known_args()
    bundle = args.bundle.resolve()
    verify(bundle)
    version = subprocess.check_output([args.bazel, "--version"], text=True).strip()
    if version != "bazel 7.6.1":
        parser.error("use Bazel 7.6.1")
    # Reject options which can change dependency sources or start remote work.
    options = extra[:extra.index("--")] if "--" in extra else extra
    for option in options:
        if option.startswith(("--registry", "--vendor", "--repository", "--override",
                              "--inject", "--remote", "--config", "--lockfile", "--enable_bzlmod",
                              "--noenable_bzlmod", "--enable_workspace", "--noenable_workspace",
                              "--experimental_downloader")):
            parser.error(f"dependency-source override is not allowed: {option}")
    output = args.output_user_root.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Bazel mutates vendor bookkeeping. Never let it alter the delivered snapshot.
    with tempfile.TemporaryDirectory(prefix="vendor-input-", dir=output) as temporary:
        vendor = Path(temporary) / "vendor"
        shutil.copytree(bundle / "vendor", vendor)
        command = [args.bazel, "--batch", "--ignore_all_rc_files", f"--output_user_root={output}",
                   args.command, "--enable_bzlmod", "--noenable_workspace", "--lockfile_mode=error",
                   f"--vendor_dir={vendor}", "--repository_disable_download",
                   f"--repository_cache={output / 'repository-cache'}", *extra]
        return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Offline build preparation error: {error}")
