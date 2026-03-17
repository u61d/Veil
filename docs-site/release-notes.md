# Release notes

## Alpha 1

Veil Alpha 1 is the first release where the current privacy claims are tied to build and runtime evidence instead of source edits alone.

### What changed

- Product telemetry defaults are off.
- Clean-profile startup no longer writes the main telemetry and data-reporting identifiers seen in stock Firefox startup.
- Clean-profile startup traffic is reduced to the retained Mozilla endpoints used for Remote Settings and content-signature.
- Push startup stays deferred on clean profiles, and the upstream `dom/push` mochitest suite still passes against the current Veil build.
- Linux builds now ship a Veil-branded launcher, desktop-entry installer, and real icon set.
- The Linux release tarball bundles the launcher, desktop-entry installer, install note, and icon assets needed for a normal local run.

### What stayed in place on purpose

- Remote Settings and content-signature traffic
- crashreporter
- narrow claim language around `MOZ_DATA_REPORTING`

### What we are not claiming

- anonymity browser
- Tor replacement
- zero network traffic
- every `MOZ_DATA_REPORTING` path removed at build time

For the release artifact itself, use the current GitHub prerelease:

- [Veil releases](https://github.com/u61d/Veil/releases)
