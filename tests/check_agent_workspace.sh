#!/usr/bin/env bash
set -euo pipefail

vbot_repo_root="${TEST_SRCDIR:?}/${TEST_WORKSPACE:?}"
exec python3 "$vbot_repo_root/tests/test_agent_workspace.py" --root "$vbot_repo_root" --runfiles
