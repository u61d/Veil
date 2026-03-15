# Veil Known Limitations

Status date: `2026-03-15`

## Current limitations

- `MOZ_DATA_REPORTING` still resolves true because upstream derives it from a crashreporter-linked aggregate.
- Clean-profile startup still reaches Mozilla-operated Remote Settings and content-signature endpoints that Veil intentionally retains for security-sensitive reasons.
- Crashreporter behavior has not been removed or redesigned in this Alpha.
- Some backup manifest metadata still carries telemetry/reporting-adjacent fields in a user-initiated backup path.
- Veil's strongest Push validation is the upstream local mochitest harness, not an external public push-service deployment.
- A fresh configure from a clean source snapshot is still sensitive to local WASI/clang toolchain state in this workspace.
- End-to-end search UI was not fully exercised in the headless Alpha smoke harness.

## Non-goals for Alpha

- No claim of strong network-layer anonymity.
- No Tor Browser equivalence.
- No advanced anti-fingerprinting package beyond the conservative work already documented.
- No removal of security-sensitive update/configuration infrastructure without replacement.
- No broad preference cleanup beyond the verified privacy/telemetry/network surfaces already in scope.

## Practical reading

Veil Alpha is meant to be honest and measurable, not maximal. The remaining caveats are mostly compile-time aggregation, retained security-sensitive services, a fresh-build environment issue, and a few user-initiated backup/reporting-adjacent paths rather than active clean-profile telemetry behavior.
