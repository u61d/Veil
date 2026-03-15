# Veil

Veil is a Firefox-based fork with a narrow goal: ship a browser that talks less in the background, turns product telemetry off by default, and stays close enough to upstream that maintenance is still realistic.

This repo is patch-managed. It does not vendor a separate long-lived browser tree. It carries the Veil patch queue, the audit notes behind it, and the scripts used to replay and verify the current Alpha state.

## What Veil Is

- A Firefox fork with product telemetry disabled by default.
- A build-backed reduction in clean-profile telemetry and data-reporting startup state.
- A measurable reduction in browser-attributed startup traffic.
- A project that keeps security-sensitive Mozilla services like Remote Settings and content-signature in place for now.

## What Veil Is Not

- Not a Tor replacement.
- Not an anonymity browser.
- Not a browser with zero background traffic.
- Not a clean compile-time removal of every `MOZ_DATA_REPORTING` surface.

## Current Alpha State

What the current Alpha evidence supports:

- `MOZ_TELEMETRY_REPORTING`, `MOZ_SERVICES_HEALTHREPORT`, and `MOZ_NORMANDY` are not defined in the Veil build.
- Clean-profile startup no longer persists the major telemetry and data-reporting identifiers seen in stock Firefox startup.
- Clean-profile startup traffic is down to the retained security-sensitive Mozilla endpoints used for Remote Settings and content-signature.
- Basic browser paths pass current smoke checks: first launch, local page load, multiple tabs, downloads, settings, temporary extension install, service workers, and private-window launch.
- Push behavior still passes the upstream `dom/push` mochitest suite against the current Veil build.

What it does not support:

- A blanket "zero telemetry" claim.
- A blanket "all core browser functionality verified" claim.
- A fresh clean-build claim in every environment. The current patch replay is clean, but a fresh configure from a clean snapshot is still sensitive to local WASI/clang toolchain state in this workspace.

## Verification

For the current Alpha bundle:

```bash
./scripts/run_alpha_readiness.sh
python3 scripts/smoke_alpha_release.py --output-json artifacts/release-verify/veil-smoke.json
```

The first command reruns the patch replay check, runtime verifier, backup-surface verifier, and clean-profile startup audit. The second runs the Alpha smoke pass.

Key docs:

- [release claims](docs/release-claims.md)
- [known limitations](docs/known-limitations.md)
- [Alpha readiness](docs/alpha-readiness.md)
- [rebase strategy](docs/rebase-strategy.md)

## Repository Layout

- `docs/`: threat model, audit matrices, release notes, maintenance notes
- `patches/`: Veil patch queue and machine-readable patch inventory
- `scripts/`: replay, verification, audit, and smoke-test helpers
- `branding/`: placeholders for redistribution assets

## Release Notes

Alpha release notes live in [RELEASE_NOTES_ALPHA.md](RELEASE_NOTES_ALPHA.md).
