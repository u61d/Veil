#!/usr/bin/env bash
set -euo pipefail

package_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
launcher="$package_root/run-veil.sh"
icon_root="$package_root/icons"
icon_sizes=(16 32 48 64 128 256 512)

if [[ ! -x "$launcher" ]]; then
  printf 'Launcher script is missing or not executable: %s\n' "$launcher" >&2
  exit 1
fi

for size in "${icon_sizes[@]}"; do
  icon_source="$icon_root/veil-icon-${size}.png"
  if [[ ! -f "$icon_source" ]]; then
    printf 'Icon is missing: %s\n' "$icon_source" >&2
    exit 1
  fi
done

data_root="${XDG_DATA_HOME:-$HOME/.local/share}"
apps_dir="$data_root/applications"
theme_root="$data_root/icons/hicolor"

mkdir -p "$apps_dir"
for size in "${icon_sizes[@]}"; do
  icons_dir="$theme_root/${size}x${size}/apps"
  mkdir -p "$icons_dir"
  install -m 0644 "$icon_root/veil-icon-${size}.png" "$icons_dir/veil.png"
done

desktop_file="$apps_dir/veil.desktop"
cat > "$desktop_file" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Veil
Comment=Privacy-first Firefox-based browser build
Exec=$launcher %u
TryExec=$launcher
Icon=veil
Terminal=false
Categories=Network;WebBrowser;
StartupNotify=true
StartupWMClass=veil
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/mailto;
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$apps_dir" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q -t "$theme_root" >/dev/null 2>&1 || true
fi

printf 'Installed %s\n' "$desktop_file"
