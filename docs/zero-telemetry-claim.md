# Veil Zero Telemetry Claim

Status date: `2026-03-15`

This document tracks what Veil has actually proven so far, not what the project eventually intends to claim.

## Current claim boundary

Veil does not yet qualify for a fully proven "zero telemetry" desktop claim.

What Veil can currently claim with build-backed and runtime-backed evidence:

- Veil's Linux build is configured with `MOZ_TELEMETRY_REPORTING=` in the Veil mozconfig.
- `scripts/verify_telemetry_runtime.py` confirms from the finished build that:
  - `MOZ_TELEMETRY_REPORTING` is not defined
  - `MOZ_SERVICES_HEALTHREPORT` is not defined
  - `MOZ_NORMANDY` is not defined
  - built `firefox.js` carries Veil's default-off telemetry, study, discovery, first-run data-reporting, region, connectivity, and captive-portal prefs
  - built `greprefs.js` lacks `datareporting.healthreport.*`, `datareporting.usage.uploadEnabled`, and `datareporting.policy.*`
  - built `BrowserComponents.manifest` no longer registers Normandy startup or shutdown handlers
  - built `xpcshell` reports `AppConstants.MOZ_TELEMETRY_REPORTING === false` and `AppConstants.MOZ_NORMANDY === false`
- Current upstream nuance: `MOZ_NORMANDY` does not by itself remove all Nimbus-related code from the compile graph. Veil treats the flag as verified startup/UI gating, not as proof that every Normandy- or Nimbus-adjacent source file vanished from the build.
- Clean-profile startup artifacts in `artifacts/network-audit/after-20260315-mozdata/summary.json` now show that Veil no longer persists:
  - `toolkit.telemetry.cachedClientID`
  - `toolkit.telemetry.cachedProfileGroupID`
  - `datareporting/state.json`
  - `datareporting.dau.cachedUsageProfileID`
  - `datareporting.dau.cachedUsageProfileGroupID`
  - `toolkit.telemetry.previousBuildID`
  - `nimbus.profileId`
  - `dom.push.userAgentID`
  - `datareporting.policy.*` first-run acceptance state
- The same reduced startup audit shows that `www.mozilla.org`, `location.services.mozilla.com`, `detectportal.firefox.com`, and `push.services.mozilla.com` are gone from clean-profile startup.
- `scripts/run_push_regression.py` plus the upstream `dom/push/test/mochitest.toml` suite prove that real service-worker Push subscription behavior still works in Veil's built browser under Mozilla's own local test harness.
- Build-backed file inspection now also shows that Veil no longer loads the data-reporting infobar at browser startup and no longer wires the telemetry/upload/studies/addon-recommendation controls into the built preferences startup paths.
- Veil-generated backups now ignore data-reporting upload prefs, policy state, and cached usage-profile IDs, so those values are no longer serialized into new backup archives by default.

## Why Veil still cannot claim zero telemetry

Startup network activity still remains for Mozilla-operated services that Veil has not removed in this run:

- `firefox.settings.services.mozilla.com`
- `firefox-settings-attachments.cdn.mozilla.net`
- `content-signature-2.cdn.mozilla.net`

That is enough to reject a blanket "minimal unsolicited network activity" claim, and `MOZ_DATA_REPORTING` still prevents an entirely clean compile-time "zero telemetry" statement even though the current clean-profile runtime artifacts no longer show telemetry or push identifiers.

## What is still only partially solved

- `MOZ_DATA_REPORTING` remains enabled because crashreporter still contributes to the aggregate upstream flag.
- `www.mozilla.org` is now source-proved as a data-reporting first-run page opened through `TelemetryReportingPolicy`, but that only fixes one reporting-policy surface.
- Push no longer initializes on clean-profile startup, and a seeded PushDB profile proves that startup re-initialization returns when persisted Push subscription state exists. Veil has now also passed the upstream Push mochitest suite, so the remaining Push caveat is no longer correctness of core subscription flows but only the absence of an external public push-service validation in this environment.

## Remaining `MOZ_DATA_REPORTING` surfaces

After the current audit, the remaining meaning of `MOZ_DATA_REPORTING` in Veil is narrow:

- `AppConstants.MOZ_DATA_REPORTING` is still `true` at build and runtime.
- `TelemetryReportingPolicy` still compiles, but current Veil defaults keep it inert on clean startup.
- The `about:preferences` data-collection section is still partly gated by `MOZ_DATA_REPORTING` because the crash auto-submit checkbox lives there.
- Backup manifest metadata still carries some telemetry/reporting-adjacent fields in a user-initiated path.

That is a compile-time and backup-schema caveat, not current evidence of active clean-profile telemetry behavior.

## Explicit non-claims

- Veil does not yet claim zero telemetry collection.
- Veil does not yet claim zero telemetry state generation.
- Veil does not yet claim minimal unsolicited network activity.
- Veil does not yet claim that crash reporting has been removed.
- Veil does not yet claim that `MOZ_DATA_REPORTING` is fully absent.
