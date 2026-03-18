#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_root="$repo_root/artifacts/releases"
arch="${VEIL_RELEASE_ARCH:-$(uname -m)}"
version_label="${VEIL_RELEASE_VERSION:-alpha1}"
bundle_name="veil-${version_label}-linux-${arch}"
bundle_root="$build_root/$bundle_name"
runtime_source=""

clean_runtime_tree() {
  local runtime_root="$1"

  rm -f "$runtime_root/.lldbinit" \
        "$runtime_root/.mkdir.done" \
        "$runtime_root/.parentlock" \
        "$runtime_root/libxul.so-gdb.py"
  rm -rf "$runtime_root/gtest" \
         "$runtime_root/gmp-fake" \
         "$runtime_root/gmp-fakeopenh264" \
         "$runtime_root/moz-src"
  rm -f "$runtime_root"/BadCertAndPinningServer \
        "$runtime_root"/DelegatedCredentialsServer \
        "$runtime_root"/EncryptedClientHelloServer \
        "$runtime_root"/EventArtifactDefinitions.json \
        "$runtime_root"/FaultyServer \
        "$runtime_root"/GenerateOCSPResponse \
        "$runtime_root"/OCSPStaplingServer \
        "$runtime_root"/SanctionsTestServer \
        "$runtime_root"/ScalarArtifactDefinitions.json \
        "$runtime_root"/ShowSSEConfig \
        "$runtime_root"/SmokeDMD \
        "$runtime_root"/WriteArgument \
        "$runtime_root"/certutil \
        "$runtime_root"/dependentlibs.list.gtest \
        "$runtime_root"/dmd.py \
        "$runtime_root"/fix_stacks.py \
        "$runtime_root"/http3server \
        "$runtime_root"/logalloc-replay \
        "$runtime_root"/nsinstall \
        "$runtime_root"/pk12util \
        "$runtime_root"/rapl \
        "$runtime_root"/screentopng \
        "$runtime_root"/signmar \
        "$runtime_root"/ssltunnel \
        "$runtime_root"/xpcshell \
        "$runtime_root"/zucchini \
        "$runtime_root"/zucchini-gtest
  rm -f "$runtime_root"/Test*
}

break_runtime_hardlinks() {
  local runtime_root="$1"
  local file
  local tmp

  while IFS= read -r -d '' file; do
    tmp="${file}.tmpcopy"
    cp --remove-destination "$file" "$tmp"
    mv "$tmp" "$file"
  done < <(find "$runtime_root" -xdev -type f -links +1 -print0)
}

normalize_runtime_binaries() {
  local runtime_root="$1"

  if [[ -f "$runtime_root/libonnxruntime.so" ]]; then
    patchelf --remove-rpath "$runtime_root/libonnxruntime.so"
  fi
}

sanitize_runtime_tree() {
  local runtime_root="$1"
  local home_path="$2"

  python - "$runtime_root" "$home_path" <<'PY'
import pathlib
import re
import sys

runtime_root = pathlib.Path(sys.argv[1])
home_path = sys.argv[2]

buildconfig = runtime_root / "chrome" / "toolkit" / "content" / "global" / "buildconfig.html"
if buildconfig.exists():
    text = buildconfig.read_text(encoding="utf-8")
    text = text.replace(home_path, "<build-path>")
    buildconfig.write_text(text, encoding="utf-8")

rfp_constants = runtime_root / "modules" / "RFPTargetConstants.sys.mjs"
if rfp_constants.exists():
    lines = rfp_constants.read_text(encoding="utf-8").splitlines()
    if len(lines) >= 2 and lines[1].startswith("// See extract_rfp_targets.py, "):
        lines[1] = (
            "// See extract_rfp_targets.py and the RFPTargets*.inc files in "
            "toolkit/components/resistfingerprinting instead."
        )
        rfp_constants.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

verify_runtime_tree() {
  local runtime_root="$1"
  local verify_log="$2"
  shift 2
  local leak_pattern
  local leak_found=0

  if find "$runtime_root" -type l -lname '/*' -print -quit | grep -q .; then
    {
      printf 'Absolute symlinks remain in the packaged runtime:\n'
      find "$runtime_root" -type l -lname '/*' | sed -n '1,40p'
    } >&2
    return 1
  fi

  if find "$runtime_root" -xdev -type f -links +1 -print -quit | grep -q .; then
    {
      printf 'Hardlinked files remain in the packaged runtime:\n'
      find "$runtime_root" -xdev -type f -links +1 -printf '%n %p\n' | sed -n '1,40p'
    } >&2
    return 1
  fi

  python - "$runtime_root" <<'PY'
import os
import sys

root = os.path.realpath(sys.argv[1])
bad = []

for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
    for name in dirnames + filenames:
        path = os.path.join(dirpath, name)
        if not os.path.islink(path):
            continue
        target = os.readlink(path)
        resolved = os.path.realpath(os.path.join(dirpath, target))
        if resolved != root and not resolved.startswith(root + os.sep):
            bad.append((os.path.relpath(path, root), target, resolved))
        if len(bad) >= 40:
            break
    if len(bad) >= 40:
        break

if bad:
    print("Symlinks escaping the package root remain:", file=sys.stderr)
    for relpath, target, resolved in bad:
        print(f"{relpath} -> {target} [{resolved}]", file=sys.stderr)
    sys.exit(1)
PY

  : > "$verify_log"
  for leak_pattern in "$@"; do
    [[ -n "$leak_pattern" ]] || continue
    if LC_ALL=C grep -R -n --binary-files=without-match -F \
      "$leak_pattern" "$runtime_root" "$bundle_root/BUILD-INFO.txt" >> "$verify_log"; then
      leak_found=1
    fi
  done

  if [[ "$leak_found" -ne 0 ]]; then
    printf 'Build-machine path leakage found in the release bundle:\n' >&2
    sed -n '1,40p' "$verify_log" >&2
    return 1
  fi
}

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

# The built runtime tree contains many symlinks back into the source tree and
# ~/.mozbuild. Dereference them here so the release bundle is self-contained.
cp -aL "$runtime_source"/. "$bundle_root/veil/"
clean_runtime_tree "$bundle_root/veil"
break_runtime_hardlinks "$bundle_root/veil"
normalize_runtime_binaries "$bundle_root/veil"
sanitize_runtime_tree "$bundle_root/veil" "$HOME"
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
Version output: $version_output
Repo commit: ${git_commit:-unknown}
Repo state: $git_state
EOF

cp "$build_note" "$bundle_root/BUILD-INFO.txt"

verify_log="$build_root/${bundle_name}.verify.txt"
rm -f "$verify_log"
verify_runtime_tree "$bundle_root/veil" "$verify_log" "$HOME" "$repo_root" "$runtime_source"
rm -f "$verify_log"

tarball="$build_root/${bundle_name}.tar.gz"
checksum_file="$tarball.sha256"

rm -f "$tarball" "$checksum_file"
tar -C "$build_root" -czf "$tarball" "$bundle_name"
(
  cd "$build_root"
  sha256sum "$(basename "$tarball")" > "$checksum_file"
)

printf '%s\n%s\n%s\n' "$tarball" "$checksum_file" "$build_note"
