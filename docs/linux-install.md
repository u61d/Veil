# Linux Install

## Extract and run

Extract the tarball and run:

```bash
./run-veil.sh
```

The launcher uses its own profile path under `~/.local/share/veil/profile` by default.

If you want a different profile location:

```bash
VEIL_PROFILE_DIR=/path/to/profile ./run-veil.sh
```

## Desktop entry and icon

To install a user-local desktop entry and the Veil icon set:

```bash
./install-desktop-entry.sh
```

This writes `veil.desktop` to `~/.local/share/applications/` and installs the Veil PNG icons into the local `hicolor` theme directories under `~/.local/share/icons/`.

## Default-handler note

The Applications settings row that says `Use Veil (default)` depends on the system handler state, not on a Veil-owned label.

If you want `mailto` to resolve to Veil on Linux:

```bash
xdg-mime default veil.desktop x-scheme-handler/mailto
```

If you want Veil to handle web links too:

```bash
xdg-mime default veil.desktop x-scheme-handler/http
xdg-mime default veil.desktop x-scheme-handler/https
```

## Caveat

The build still uses the retained Mozilla services Veil depends on for Remote Settings and content-signature. The Linux package does not change that.
