#!/usr/bin/env bash
set -euo pipefail

package_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime_dir="$package_root/veil"

if [[ -x "$runtime_dir/veil" ]]; then
  binary="$runtime_dir/veil"
elif [[ -x "$runtime_dir/firefox" ]]; then
  binary="$runtime_dir/firefox"
else
  printf 'No Veil runtime found under %s\n' "$runtime_dir" >&2
  exit 1
fi

profile_dir="${VEIL_PROFILE_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/veil/profile}"
mkdir -p "$profile_dir"

export LD_LIBRARY_PATH="$runtime_dir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export MOZ_APP_REMOTINGNAME="${VEIL_REMOTING_NAME:-veil}"

exec "$binary" --new-instance --profile "$profile_dir" "$@"
