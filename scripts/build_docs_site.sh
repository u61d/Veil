#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdocs_cmd="mkdocs"

if [[ -x "$repo_root/.venv-docs/bin/mkdocs" ]]; then
  mkdocs_cmd="$repo_root/.venv-docs/bin/mkdocs"
fi

NO_MKDOCS_2_WARNING=1 "$mkdocs_cmd" build --strict
touch "$repo_root/site/.nojekyll"
