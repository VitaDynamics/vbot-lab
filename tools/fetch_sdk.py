"""Download pinned SDK Release assets explicitly; never install, build or deploy."""

import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from container_context import require_dev_container
from sdk_assets import configuration, digest, wheel_names


def fetch(config, output, names=None, *, transport="https"):
    sdk = config["sdk"]
    if sdk["repository"] != "VitaDynamics/vbot-lab":
        raise ValueError("SDK downloads must use the configured VBOT Lab Release repository")
    if transport not in ("https", "gh"):
        raise ValueError("unsupported download transport")
    output.mkdir(parents=True, exist_ok=True)
    for item in sdk["assets"]:
        if names is not None and item["name"] not in names:
            continue
        destination = output / item["name"]
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or not destination.is_file() or digest(destination) != item["sha256"]:
                raise ValueError(f"existing asset is invalid; inspect it before retrying: {item['name']}")
            continue
        url = (f'https://github.com/{sdk["repository"]}/releases/download/'
               f'{quote(sdk["release_tag"], safe="")}/{quote(item["name"], safe="")}')
        with tempfile.NamedTemporaryFile(dir=output, prefix=".sdk-download-", delete=False) as stream:
            temporary = Path(stream.name)
            try:
                if transport == "gh":
                    # Authentication stays in GitHub CLI. Never construct token-bearing URLs
                    # or echo its potentially sensitive stderr. Only our temporary file may be replaced.
                    stream.close()
                    try:
                        result = subprocess.run(
                            ["gh", "release", "download", sdk["release_tag"], "--repo", sdk["repository"],
                             "--pattern", item["name"], "--output", str(temporary), "--clobber"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=120)
                    except FileNotFoundError:
                        raise ValueError("GitHub CLI is unavailable; download the matching Release assets "
                                         "in your browser into the output directory, then retry") from None
                    except subprocess.TimeoutExpired:
                        raise ValueError(f'GitHub CLI download timed out: {item["name"]}') from None
                    if result.returncode:
                        raise ValueError(f'GitHub CLI download failed: {item["name"]}; check authorization '
                                         'and access to the configured Release')
                    if temporary.stat().st_size > 128 * 1024 * 1024:
                        raise ValueError("SDK asset exceeds download limit")
                else:
                    try:
                        response = urlopen(url, timeout=60)
                    except HTTPError as error:
                        raise ValueError(f'SDK asset download failed: {item["name"]} (HTTP {error.code}); '
                                         'for authorized GitHub access use --transport gh, or download '
                                         'the matching assets in your browser') from None
                    with response:
                        size = 0
                        for block in iter(lambda: response.read(1024 * 1024), b""):
                            size += len(block)
                            if size > 128 * 1024 * 1024:
                                raise ValueError("SDK asset exceeds download limit")
                            stream.write(block)
                    stream.flush()
                if digest(temporary) != item["sha256"]:
                    raise ValueError(f'SDK asset checksum mismatch: {item["name"]}')
                # Exclusive publication also rejects a destination created during the download.
                os.link(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", choices=("python", "all"), default="python")
    parser.add_argument("--platform", choices=("linux_aarch64", "linux_x86_64", "macosx_11_0_arm64"), default="linux_aarch64")
    parser.add_argument("--transport", choices=("https", "gh"), default="https",
                        help="HTTPS or authenticated GitHub CLI; matching local assets are reused first")
    args = parser.parse_args(argv)
    try:
        require_dev_container()
        config = configuration()
        names = None if args.profile == "all" else {
            *wheel_names(config, args.platform).values(), "EDU_SDK_MANIFEST.json", "SHA256SUMS",
            f'flatbuffers-{config["sdk"]["python"]["wheels"]["flatbuffers"]}.LICENSE'}
        fetch(config, args.output.resolve(), names, transport=args.transport)
        print("Pinned SDK assets ready; no packages installed and no device contacted.")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
