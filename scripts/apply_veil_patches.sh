#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
upstream_dir="${1:-$repo_root/upstream/firefox}"
mode="${2:-apply}"

if [[ ! -d "$upstream_dir" ]]; then
  printf 'Upstream checkout not found: %s\n' "$upstream_dir" >&2
  exit 1
fi

mapfile -t patch_paths < <(
  python3 - "$repo_root/patches/patch-inventory.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    inventory = json.load(fh)

for patch in inventory["patches"]:
    if patch["status"] == "authored" and patch["path"]:
        print(patch["path"])
PY
)

for rel_path in "${patch_paths[@]}"; do
  patch_path="$repo_root/$rel_path"
  printf 'Applying %s\n' "$rel_path"
  if [[ "$mode" == "--check" ]]; then
    patch -p1 -d "$upstream_dir" --dry-run < "$patch_path"
  else
    patch -p1 -d "$upstream_dir" < "$patch_path"
  fi
done

printf 'Processed %d patch(es)\n' "${#patch_paths[@]}"
