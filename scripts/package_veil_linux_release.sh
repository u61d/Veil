#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_root="$repo_root/artifacts/releases"
arch="${VEIL_RELEASE_ARCH:-$(uname -m)}"
version_label="${VEIL_RELEASE_VERSION:-alpha1}"
bundle_name="veil-${version_label}-linux-${arch}"
bundle_root="$build_root/$bundle_name"
runtime_source=""

if [[ -n "${VEIL_RUNTIME_SOURCE:-}" ]]; then
  runtime_source="$VEIL_RUNTIME_SOURCE"
else
  mapfile -t candidates < <(
    find "$repo_root/upstream" -path '*/obj-veil/dist/bin' -type d | sort
  )
  if [[ "${#candidates[@]}" -gt 0 ]]; then
    runtime_source="${candidates[0]}"
  fi
fi

if [[ -z "$runtime_source" || ! -d "$runtime_source" ]]; then
  printf 'No built Veil runtime found.\n' >&2
  exit 1
fi

icon_root="$repo_root/branding/icons"
for size in 16 32 48 64 128 256 512; do
  if [[ ! -f "$icon_root/veil-icon-${size}.png" ]]; then
    printf 'Missing icon asset: %s\n' "$icon_root/veil-icon-${size}.png" >&2
    exit 1
  fi
done

rm -rf "$bundle_root"
mkdir -p "$bundle_root/veil" "$bundle_root/icons"

cp -a "$runtime_source"/. "$bundle_root/veil/"
cp -a "$icon_root"/. "$bundle_root/icons/"
install -m 0755 "$repo_root/packaging/linux/run-veil.sh" "$bundle_root/run-veil.sh"
install -m 0755 "$repo_root/packaging/linux/install-desktop-entry.sh" "$bundle_root/install-desktop-entry.sh"
install -m 0644 "$repo_root/docs/linux-install.md" "$bundle_root/README-Linux.md"

# Keep the packaged runtime icon files in sync with the tracked release assets.
for size in 16 32 48 64 128; do
  install -m 0644 "$icon_root/veil-icon-${size}.png" \
    "$bundle_root/veil/browser/chrome/icons/default/default${size}.png"
done
install -m 0644 "$icon_root/veil-icon-32.png" \
  "$bundle_root/veil/browser/chrome/browser/content/branding/icon32.png"

binary="$bundle_root/veil/veil"
if [[ ! -x "$binary" && -x "$bundle_root/veil/firefox" ]]; then
  binary="$bundle_root/veil/firefox"
fi

if [[ ! -x "$binary" ]]; then
  printf 'Packaged Veil binary is missing.\n' >&2
  exit 1
fi

version_output="$(
  LD_LIBRARY_PATH="$bundle_root/veil" "$binary" --version
)"

git_commit="$(git -C "$repo_root" rev-parse --short HEAD 2>/dev/null || true)"
if [[ -n "$(git -C "$repo_root" status --short 2>/dev/null || true)" ]]; then
  git_state="dirty"
else
  git_state="clean"
fi

build_note="$build_root/${bundle_name}.build.txt"
cat > "$build_note" <<EOF
Veil Linux release bundle
Bundle: $bundle_name
Created (UTC): $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Runtime source: $runtime_source
Version output: $version_output
Repo commit: ${git_commit:-unknown}
Repo state: $git_state
EOF

cp "$build_note" "$bundle_root/BUILD-INFO.txt"

tarball="$build_root/${bundle_name}.tar.gz"
checksum_file="$tarball.sha256"

rm -f "$tarball" "$checksum_file"
tar -C "$build_root" -czf "$tarball" "$bundle_name"
(
  cd "$build_root"
  sha256sum "$(basename "$tarball")" > "$checksum_file"
)

printf '%s\n%s\n%s\n' "$tarball" "$checksum_file" "$build_note"
