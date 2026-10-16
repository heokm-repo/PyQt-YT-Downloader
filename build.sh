#!/usr/bin/env bash
# Windows Git Bash entry point; the application remains Windows-only.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec "${PYTHON:-python}" -B -m build_scripts.build_release "$@"
