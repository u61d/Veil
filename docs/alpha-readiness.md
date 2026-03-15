# Veil Alpha Readiness

Status date: `2026-03-15`

This document defines what Veil Alpha means technically and what must remain explicit in release notes and maintainer handoff.

## Alpha position

Veil Alpha is ready as a technical milestone for a privacy-first Firefox fork with:

- build-backed compile-time reduction of telemetry/study surfaces
- clean-profile suppression of the major telemetry/data-reporting identifiers previously observed at startup
- reduced unsolicited startup traffic, with only the intentionally retained security-sensitive Mozilla endpoints still browser-attributed
- real Push regression evidence from the upstream `dom/push` mochitest suite
- patch-queue replay checks and rerunnable verification scripts

## Alpha claim boundary

Veil Alpha is:

- a private browser effort
- a hardened browser effort
- a Firefox-based fork with reduced phoning-home behavior

Veil Alpha is not:

- a zero-telemetry browser in the absolute compile-time sense
- a Tor replacement
- an anonymity browser
- a browser with zero background network traffic

## Alpha technical readiness gate

Veil Alpha is technically ready when all of the following remain true:

- the current Veil patch queue replays cleanly onto a fresh upstream snapshot
- the build-backed runtime verifier passes
- the backup-surface verifier passes
- the clean-profile startup audit still shows only the intentionally retained security-sensitive endpoints
- release claims and known limitations match the latest artifacts

## One-command verification

Use:

```bash
./scripts/run_alpha_readiness.sh
```

The script reruns:

- the runtime verifier
- the backup-surface verifier
- the clean-profile startup network audit
- the full patch replay check

It writes a timestamped artifact bundle under `artifacts/alpha-readiness/`.
