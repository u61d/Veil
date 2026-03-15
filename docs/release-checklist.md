# Veil Release Checklist

Status date: `2026-03-15`

## Alpha technical checklist

- [ ] Verify the current upstream revision is recorded for the release.
- [ ] Re-run `./scripts/run_alpha_readiness.sh`.
- [ ] Re-run `python3 scripts/smoke_alpha_release.py --output-json artifacts/release-verify/veil-smoke.json`.
- [ ] Confirm the runtime verifier passes.
- [ ] Confirm the backup-surface verifier passes.
- [ ] Confirm the clean-profile startup audit still shows only the retained security-sensitive endpoints.
- [ ] Confirm the patch replay check succeeds on a fresh upstream snapshot.
- [ ] Confirm Push regression evidence still points at a passing upstream `dom/push` mochitest artifact.
- [ ] Confirm any fresh-build or fresh-configure failure is either fixed or called out explicitly in the release notes.

## Alpha documentation checklist

- [ ] Review [docs/release-claims.md](/home/null2ud/Projects/Veil/docs/release-claims.md) against the newest artifacts.
- [ ] Review [docs/known-limitations.md](/home/null2ud/Projects/Veil/docs/known-limitations.md) for anything newly discovered.
- [ ] Review [docs/release-verification.md](/home/null2ud/Projects/Veil/docs/release-verification.md) so the release text matches the current evidence.
- [ ] Review [docs/zero-telemetry-claim.md](/home/null2ud/Projects/Veil/docs/zero-telemetry-claim.md) for claim drift.
- [ ] Review [docs/network-audit-matrix.md](/home/null2ud/Projects/Veil/docs/network-audit-matrix.md) and [docs/telemetry-audit-matrix.md](/home/null2ud/Projects/Veil/docs/telemetry-audit-matrix.md) for stale paths or stale status text.

## Alpha stop-ship triggers

- [ ] Any new clean-profile telemetry/data-reporting identifier appears.
- [ ] Any new unsolicited startup endpoint appears beyond the retained security-sensitive set.
- [ ] Patch replay fails on a fresh upstream snapshot.
- [ ] Release text implies a clean fresh build when the current build path still needs local environment caveats.
- [ ] Release notes or marketing text overclaim beyond the current measured boundary.
