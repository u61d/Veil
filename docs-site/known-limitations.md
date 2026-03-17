# Known limitations

## Current limits

- `MOZ_DATA_REPORTING` still resolves true because upstream derives it from a crashreporter-linked aggregate.
- Clean-profile startup still reaches Mozilla-operated Remote Settings and content-signature endpoints that Veil intentionally retains.
- Crashreporter behavior has not been removed or redesigned in this Alpha.
- Some backup metadata still carries telemetry/reporting-adjacent fields in a user-initiated backup path.
- A fresh configure from a clean source snapshot is still sensitive to local WASI/clang toolchain state in this workspace.
- End-to-end search UI was not fully exercised in the current headless smoke harness.

## Non-goals for Alpha

- No anonymity claim.
- No Tor Browser equivalence.
- No claim of zero network traffic.
- No removal of security-sensitive update/configuration infrastructure without replacement.
- No broad preference cleanup outside the measured telemetry/network/privacy work already in scope.

## Practical read

Veil Alpha is trying to be measurable and explicit, not maximal. The remaining caveats are mostly retained security-sensitive services, compile-time aggregation around crashreporter, and a few environment-specific build edges.
