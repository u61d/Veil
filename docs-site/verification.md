# Verification

Veil's current claims are supposed to be rerunnable, not just descriptive.

## Core checks

From the repo root:

```bash
./scripts/run_alpha_readiness.sh
python3 scripts/smoke_alpha_release.py --output-json artifacts/release-verify/veil-smoke.json
```

The first command reruns:

- the runtime verifier
- the backup-surface verifier
- the clean-profile startup network audit
- the patch replay check

The second command reruns the Alpha smoke pass.

## Linux release packaging

The Linux release bundle is assembled with:

```bash
./scripts/package_veil_linux_release.sh
```

That creates the tarball, checksum, and short build note used for the GitHub prerelease asset.

## What the current evidence covers

The current public boundary is supported by:

- patch replay on a fresh upstream snapshot
- packaged runtime verification
- clean-profile startup audit artifacts
- smoke tests for basic browsing paths
- Push regression coverage from the upstream `dom/push` mochitest suite
- a tarball smoke pass against the released Linux package

## Current caveats

- The headless smoke harness still does not prove the interactive search UI end to end.
- The current workspace build path is still sensitive to local toolchain state outside the wrapper flow.

## Deeper release notes

The detailed release verification note stays in the repo:

- [release verification](https://github.com/u61d/Veil/blob/main/docs/release-verification.md)
- [release claims](https://github.com/u61d/Veil/blob/main/docs/release-claims.md)
