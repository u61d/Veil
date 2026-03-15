# GitHub Release Draft

## Title

`Veil Alpha 1`

## Body

Veil Alpha 1 is the first public Veil release where the current privacy claims are tied to build and runtime checks instead of source edits alone.

What this release does:

- disables product telemetry by default
- suppresses the main telemetry and data-reporting startup state we saw in stock Firefox startup
- reduces clean-profile startup traffic to the retained Mozilla endpoints used for Remote Settings and content-signature
- keeps the Mozilla update and configuration services it still depends on

What this release does not claim:

- not anonymous
- not a Tor replacement
- not zero network traffic
- not a full compile-time removal of every `MOZ_DATA_REPORTING` path

Current caveats:

- `MOZ_DATA_REPORTING` still resolves true because upstream ties it to crashreporter in the current aggregate
- Remote Settings and content-signature traffic are still present by design
- a fresh configure from a clean source snapshot is still sensitive to local WASI/clang toolchain state in this workspace
- the headless smoke harness did not exercise the end-to-end search UI

Verification notes:

- Veil patch replay still applies cleanly to a fresh upstream snapshot
- the packaged Veil runtime still passes the current runtime verifier and startup network audit
- the upstream `dom/push` mochitest suite still passes against the current Veil build
- a stock Firefox run on the same machine still creates substantially more startup state and startup traffic than Veil

Relevant docs:

- [README](README.md)
- [Release claims](docs/release-claims.md)
- [Known limitations](docs/known-limitations.md)
- [Release verification](docs/release-verification.md)
