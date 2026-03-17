# Linux

The packaged Linux release is meant to be extracted and run locally. It is not a system-wide installer.

## Run the tarball

```bash
./run-veil.sh
```

By default this uses a separate profile path under:

```text
~/.local/share/veil/profile
```

If you want a different profile location:

```bash
VEIL_PROFILE_DIR=/path/to/profile ./run-veil.sh
```

## Install the desktop entry and icons

```bash
./install-desktop-entry.sh
```

This installs:

- `veil.desktop` under `~/.local/share/applications/`
- the Veil PNG icon set under `~/.local/share/icons/hicolor/`

## Default-handler note

The Applications settings label `Use Veil (default)` depends on the desktop's current handler state.

If you want `mailto` to resolve to Veil:

```bash
xdg-mime default veil.desktop x-scheme-handler/mailto
```

If you want Veil to handle web links too:

```bash
xdg-mime default veil.desktop x-scheme-handler/http
xdg-mime default veil.desktop x-scheme-handler/https
```

## Current caveat

The Linux package does not remove the retained Mozilla services used for Remote Settings and content-signature. That traffic is still part of the current Alpha boundary.
