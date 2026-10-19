"""Execute an explicit development command only in a declared container context."""

import argparse
import subprocess
import sys

from container_context import require_dev_container


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        parser.error("provide a command after --")
    try:
        require_dev_container()
        result = subprocess.run(command, check=False)
        return result.returncode if result.returncode >= 0 else 128 - result.returncode
    except (OSError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
