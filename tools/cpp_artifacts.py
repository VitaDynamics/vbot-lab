"""Inspect ARM64 ELF files and their target-runtime dependencies; never execute them."""

from pathlib import Path
import re
import struct
import subprocess


def require_arm64(path):
    with Path(path).open("rb") as stream:
        header = stream.read(64)
    if len(header) != 64 or header[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", header, 18)[0] != 183:
        raise ValueError(f"expected a little-endian ARM64 ELF: {Path(path).name}")


def _read(command):
    return subprocess.run(command, check=True, capture_output=True, text=True, timeout=15,
                          env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}).stdout


def inspect_arm64(binaries, sdk_dir):
    """Resolve DT_NEEDED against ARM64 SDK/compiler libraries, not the robot's runtime."""
    pending = [(Path(path).resolve(), True) for path in binaries]
    seen = {}
    while pending:
        path, executable = pending.pop()
        require_arm64(path)
        if path in seen:
            continue
        dynamic = _read(["/usr/bin/aarch64-linux-gnu-readelf", "--wide", "--dynamic", str(path)])
        needed = re.findall(r"\(NEEDED\).*?\[([^\]]+)\]", dynamic)
        program = _read(["/usr/bin/aarch64-linux-gnu-readelf", "--wide", "--program-headers", str(path)])
        interpreter = re.findall(r"Requesting program interpreter: ([^\]]+)\]", program)
        if executable and interpreter != ["/lib/ld-linux-aarch64.so.1"]:
            raise ValueError(f"unexpected ARM64 executable interpreter: {path.name}")
        versions = _read(["/usr/bin/aarch64-linux-gnu-readelf", "--wide", "--version-info", str(path)])
        needs = versions.split("Version needs section", 1)[-1] if "Version needs section" in versions else ""
        glibc = re.findall(r"Name: GLIBC_([0-9.]+)", needs)
        if any(tuple(map(int, value.split("."))) > (2, 35) for value in glibc):
            raise ValueError(f"GLIBC requirement exceeds Ubuntu 22.04 target: {path.name}")
        seen[path] = {"file": path.parent.name + "/" + path.name, "machine": "aarch64", "needed": needed,
                      "executable": executable,
                      "interpreter": interpreter[0] if interpreter else None, "glibc_requirements": sorted(set(glibc))}
        for name in needed:
            if not re.fullmatch(r"[A-Za-z0-9_.+-]+", name) or ".." in name:
                raise ValueError("unsafe ELF dependency name")
            library = Path(sdk_dir) / "lib" / name
            if not library.is_file():
                located = _read(["/usr/bin/aarch64-linux-gnu-g++", "-print-file-name=" + name]).strip()
                library = Path(located)
                if not library.is_absolute() or not library.is_file():
                    raise ValueError(f"unresolved ARM64 runtime dependency: {name}")
            pending.append((library.resolve(), False))
    return list(seen.values())
