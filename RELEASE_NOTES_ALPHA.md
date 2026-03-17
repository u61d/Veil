# Veil Alpha 1

Veil Alpha is the first release where the current privacy claims are tied to build and runtime evidence rather than source edits alone.

## What Changed

- Product telemetry defaults are off.
- Clean-profile startup no longer writes the main telemetry and data-reporting identifiers that showed up in stock Firefox startup.
- Clean-profile startup traffic is reduced to the retained Mozilla endpoints used for Remote Settings and content-signature.
- Push startup stays deferred on clean profiles, and the upstream `dom/push` mochitest suite still passes against the current Veil build.
- Alpha smoke checks pass for first launch, browsing, tabs, downloads, settings, temporary extensions, service workers, and private-window launch.
- Linux local builds now have a Veil-branded launcher script, a separate default profile path, and a user-local desktop entry installer.
- The Linux launcher now exports `MOZ_APP_REMOTINGNAME=veil` so local menu and window matching do not reuse the stock Firefox instance name.
- The Linux installer and runtime branding now use the provided Veil PNG icon set instead of the earlier local placeholder icon.
- The Linux release tarball bundles `run-veil.sh`, `install-desktop-entry.sh`, `README-Linux.md`, and the Veil icon set for a normal local install.

## What We Verified

- Veil patch replay still applies cleanly to a fresh upstream source snapshot.
- The built Veil runtime still matches the current telemetry and startup-network assertions.
- A clean-profile startup no longer creates `datareporting/state.json` in the current Veil build.
- A stock Firefox run on the same machine still creates telemetry/data-reporting/Nimbus state and makes substantially more startup connections than Veil.

## What We Are Not Claiming

- We are not calling Veil anonymous.
- We are not calling it a Tor replacement.
- We are not claiming zero network traffic.
- We are not claiming every `MOZ_DATA_REPORTING` path is gone at build time.

## Known Limits In This Alpha

- `MOZ_DATA_REPORTING` is still true because upstream ties it to crashreporter in the current aggregate.
- Remote Settings and content-signature traffic are still present by design.
- Crashreporter is still present.
- End-to-end search UI was not fully exercised in headless automation; the headless harness limitation is the same in stock Firefox on this machine.
- A fresh configure from a clean source snapshot is still sensitive to local WASI/clang toolchain state in this workspace.

## Files To Read Before Shipping

- [docs/release-claims.md](docs/release-claims.md)
- [docs/known-limitations.md](docs/known-limitations.md)
- [docs/alpha-readiness.md](docs/alpha-readiness.md)
