#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
upstream_dir="${1:-$repo_root/upstream/firefox}"
objdir="${2:-$upstream_dir/obj-veil}"
duration="${VEIL_AUDIT_DURATION:-20}"
dist_bin="$objdir/dist/bin"

if [[ ! -d "$upstream_dir" ]]; then
  printf 'missing upstream source tree: %s\n' "$upstream_dir" >&2
  exit 1
fi

if [[ ! -d "$objdir" ]]; then
  printf 'missing objdir: %s\n' "$objdir" >&2
  exit 1
fi

browser="$dist_bin/firefox"
if [[ ! -x "$browser" ]]; then
  printf 'missing browser binary: %s\n' "$browser" >&2
  exit 1
fi

if [[ -n "${VEIL_UPSTREAM_ARCHIVE:-}" ]]; then
  archive_path="$VEIL_UPSTREAM_ARCHIVE"
else
  archive_path="$(
    find "$repo_root/upstream" -maxdepth 1 -type f -name 'firefox-*.tar.gz' -printf '%T@ %p\n' \
      | sort -n \
      | tail -n 1 \
      | cut -d' ' -f2-
  )"
fi
if [[ -z "$archive_path" ]]; then
  printf 'missing upstream source archive under %s/upstream\n' "$repo_root" >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
run_dir="$repo_root/artifacts/alpha-readiness/$timestamp"
mkdir -p "$run_dir"

export LD_LIBRARY_PATH="$dist_bin${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

printf 'Alpha readiness output: %s\n' "$run_dir"

python3 "$repo_root/scripts/verify_telemetry_runtime.py" \
  "$objdir" \
  --output-json "$run_dir/telemetry-runtime.json" \
  | tee "$run_dir/telemetry-runtime.log"

python3 "$repo_root/scripts/verify_backup_datareporting_surfaces.py" \
  --srcdir "$upstream_dir" \
  --objdir "$objdir" \
  --output-json "$run_dir/backup-datareporting.json" \
  | tee "$run_dir/backup-datareporting.log"

python3 "$repo_root/scripts/audit_network_baseline.py" \
  "$browser" \
  "$run_dir/network-audit" \
  --duration "$duration" \
  | tee "$run_dir/network-audit.log"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
tar -xf "$archive_path" -C "$tmpdir"
shopt -s nullglob
entries=("$tmpdir"/*)
shopt -u nullglob

if [[ "${#entries[@]}" -ne 1 || ! -d "${entries[0]}" ]]; then
  printf 'unexpected extracted archive layout under %s\n' "$tmpdir" >&2
  exit 1
fi

srcdir="${entries[0]}"

"$repo_root/scripts/apply_veil_patches.sh" "$srcdir" --check \
  | tee "$run_dir/patch-replay-check.log"

printf '\nCompleted Veil Alpha readiness run.\n'
printf 'Telemetry verifier: %s\n' "$run_dir/telemetry-runtime.json"
printf 'Backup verifier: %s\n' "$run_dir/backup-datareporting.json"
printf 'Network audit: %s\n' "$run_dir/network-audit/summary.json"
printf 'Patch replay log: %s\n' "$run_dir/patch-replay-check.log"
