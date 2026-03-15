# Veil Rebase Strategy

## Goals

- keep Veil patches small and categorized
- make upstream release rebases routine instead of archaeological work
- detect conflicts in the files Veil actually touches

## Patch organization

Veil patches are tracked in `patches/patch-inventory.json` with:

- stable patch ID
- category
- title
- status
- upstream files touched
- verification hooks

Current categories:

- telemetry
- network-behavior
- privacy-defaults
- anti-fingerprinting
- branding
- build-release
- tests
- docs

## Suggested workflow

1. Bootstrap or update the upstream Firefox checkout with `scripts/bootstrap_upstream_firefox.sh`.
2. Record the upstream revision used for a Veil work cycle.
3. Apply authored patches with `scripts/apply_veil_patches.sh`.
4. Run `python3 scripts/verify_telemetry_source_assertions.py`.
5. Before rebasing, compare upstream file churn against Veil-touched files with `python3 scripts/list_patch_conflicts.py`.
6. Re-run source assertions and later browser/runtime audits after conflicts are resolved.

## Conflict detection rule

If upstream changed a file touched by a Veil patch, that patch must be reviewed even if it still applies cleanly. Silent semantic drift is the main maintenance risk.

## Alpha recheck set

After each upstream rebase, re-run:

```bash
./scripts/run_alpha_readiness.sh
```

At minimum, maintainers must recheck:

- `scripts/verify_telemetry_runtime.py`
- `scripts/verify_backup_datareporting_surfaces.py`
- `scripts/audit_network_baseline.py`
- `scripts/apply_veil_patches.sh --check`

If any of those results change, update:

- release claims
- known limitations
- telemetry/network audit docs
- patch inventory entries for any patch whose behavior or verification changed

## Planned next improvements

- record tested upstream revision in machine-readable form
- add clean-profile runtime tests once Veil builds
- add packet-capture-backed network baseline checks
- split large pref-only patches into smaller topic patches as the patch queue grows
