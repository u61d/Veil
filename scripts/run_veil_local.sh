#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -n "${VEIL_BINARY:-}" ]]; then
  binary="$VEIL_BINARY"
else
  mapfile -t candidates < <(
    find "$repo_root/upstream" \( -path '*/obj-veil/dist/bin/veil' -o -path '*/obj-veil/dist/bin/firefox' \) -type f | sort
  )
  if [[ "${#candidates[@]}" -eq 0 ]]; then
    printf 'No Veil runtime found under %s/upstream\n' "$repo_root" >&2
    printf 'Build Veil first or set VEIL_BINARY to a built Veil binary.\n' >&2
    exit 1
  fi
  binary="${candidates[0]}"
fi

if [[ ! -x "$binary" ]]; then
  printf 'Veil binary is not executable: %s\n' "$binary" >&2
  exit 1
fi

profile_dir="${VEIL_PROFILE_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/veil/profile}"
mkdir -p "$profile_dir"

binary_dir="$(cd "$(dirname "$binary")" && pwd)"
export LD_LIBRARY_PATH="$binary_dir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export MOZ_APP_REMOTINGNAME="${VEIL_REMOTING_NAME:-veil}"

exec "$binary" --new-instance --profile "$profile_dir" "$@"
