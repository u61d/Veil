# MOZ_DATA_REPORTING Dependency Map

Status date: `2026-03-15`

This note maps what currently keeps `MOZ_DATA_REPORTING` enabled in Veil's build and what the flag actually gates in the current upstream source.

## Why `MOZ_DATA_REPORTING` still resolves true

`toolkit/moz.configure` derives `MOZ_DATA_REPORTING` from four inputs:

- `MOZ_TELEMETRY_REPORTING`
- `MOZ_SERVICES_HEALTHREPORT`
- `--enable-crashreporter`
- `MOZ_NORMANDY`

Veil already disables the first three browser-product telemetry/study inputs at build time:

- `MOZ_TELEMETRY_REPORTING`: disabled
- `MOZ_SERVICES_HEALTHREPORT`: disabled
- `MOZ_NORMANDY`: disabled
- crashreporter: still enabled

That means crashreporter is the remaining reason `MOZ_DATA_REPORTING` stays defined in the current Veil build.

## Current source-backed uses of `MOZ_DATA_REPORTING`

These are the non-test uses verified in the current upstream tree, now classified by Veil runtime reachability.

### Build/config layer

- `toolkit/moz.configure`
  - defines the aggregate flag
- `toolkit/modules/AppConstants.sys.mjs`
  - exposes `AppConstants.MOZ_DATA_REPORTING`

### Runtime and UI surfaces

| Surface | Source owner | Veil runtime reachability | Current status |
| --- | --- | --- | --- |
| `datareporting.policy.*` default prefs in `greprefs.js` | `modules/libpref/init/all.js` | 5. removable without affecting crash handling | Removed from built defaults by `VEIL-0205`. Veil now emits those prefs only when both `MOZ_DATA_REPORTING` and `MOZ_TELEMETRY_REPORTING` are true. |
| Data-submission infobar script load | `browser/base/content/browser-main.js` | 3. still runtime-active before `VEIL-0204` | Removed. Veil no longer loads `browser-data-submission-info-bar.js`. |
| Data-submission infobar init | `browser/base/content/browser-init.js` | 3. still runtime-active before `VEIL-0204` | Removed. Veil no longer calls `gDataNotificationInfoBar.init()`. |
| Telemetry/upload/studies/addon recommendation controls | `browser/components/preferences/privacy.inc.xhtml` | 2. still user-visible before `VEIL-0204` | Removed. Crashreporter controls remain separate. |
| Telemetry/upload/studies/addon recommendation wiring | `browser/components/preferences/privacy.js` | 3. runtime-active when the preferences page loads | Neutralized. Veil no longer wires the removed controls during preferences init. |
| Shared-profile data-reporting pref sharing | `browser/components/profiles/SelectableProfileService.sys.mjs` | 5. removable without affecting crash handling | Removed by `VEIL-0205`. Telemetry/data-reporting prefs are no longer treated as permanently shared profile-group state. |
| Cross-profile infobar tracking for data-reporting prefs | `browser/components/asrouter/modules/ASRouterTriggerListeners.sys.mjs` | 5. removable without affecting crash handling | Removed by `VEIL-0205`. Veil no longer tracks data-reporting pref flips as a cross-profile trigger. |
| Messaging-system writes to data-reporting prefs | `toolkit/components/messaging-system/lib/SpecialMessageActions.sys.mjs` | 5. removable without affecting crash handling | Removed by `VEIL-0205`. Messaging actions can no longer set those data-reporting policy prefs through the allowlist. |
| Backup serialization of data-reporting prefs and policy state | `browser/components/backup/resources/PreferencesBackupResource.sys.mjs` | 3. runtime-reachable but only when the user creates a backup | Neutralized by `VEIL-0206` for Veil-generated backups. The backup exporter now ignores `datareporting.healthreport.uploadEnabled`, `datareporting.usage.uploadEnabled`, `datareporting.policy.*`, and the cached data-reporting usage-profile IDs. |
| Backup manifest metadata carrying telemetry/reporting state | `browser/components/backup/BackupService.sys.mjs`, `browser/components/backup/content/BackupManifest.*.schema.json`, `browser/components/backup/content/restore-from-backup.mjs` | 4. coupled strongly enough to backup schema/restore metrics that removal is unsafe right now | Deferred. `legacyClientID` is schema-required, `healthTelemetryEnabled` is still read by restore UI code, and this path is user-initiated backup flow rather than clean-profile startup behavior. |
| Selectable-profile DAU group identifier plumbing | `browser/components/profiles/SelectableProfileService.sys.mjs` | 1. inert under current Veil defaults for clean profiles; only relevant when selectable-profile state already exists | Deferred. Veil no longer creates the related clean-profile identifiers on startup, but the profile-service compatibility plumbing still exists. |
| Runtime policy evaluator | `toolkit/components/telemetry/app/TelemetryReportingPolicy.sys.mjs`, `browser/components/BrowserGlue.sys.mjs`, `browser/components/StartupTelemetry.sys.mjs` | 1. harmless dead surface under current Veil defaults | Deferred. Still compiled because `MOZ_DATA_REPORTING` remains true, but current Veil defaults keep `dataSubmissionEnabled=false`, `dataSubmissionPolicyBypassNotification=true`, and `firstRunURL=""`, so the clean-profile runtime artifact shows no first-run fetch or acceptance state. |
| Pref-branch registration | `modules/libpref/Preferences.cpp` | 1. harmless infrastructure residue | Deferred. The branch registration remains compiled, but the policy prefs are no longer emitted in built defaults and are not runtime-active in Veil's clean-profile artifact. |
| Build-time `AppConstants.MOZ_DATA_REPORTING` | `toolkit/modules/AppConstants.sys.mjs` | 6. compile-time constant still visible to runtime code | Deferred. Still true while crashreporter remains in the aggregate. |
| `about:preferences` data-collection section gate | `browser/components/preferences/privacy.js`, `browser/components/preferences/preferences.xhtml` | 4. crashreporter-coupled strongly enough that removal is unsafe right now | Deferred. The built UI now proves the upload/studies controls are gone while `automaticallySubmitCrashesBox` remains. A future aggregate split would need a targeted refactor so crash UI survives without `MOZ_DATA_REPORTING`. |

## What the flag does not directly gate

The current tree does not show `MOZ_DATA_REPORTING` as the primary switch for crash submission internals.

Crash-reporting behavior is separately controlled through:

- `MOZ_CRASHREPORTER`
- `browser.crashReports.*` prefs
- `toolkit/crashreporter/*`
- browser-side crash handlers such as `browser/modules/ContentCrashHandlers.sys.mjs`

That means `MOZ_DATA_REPORTING` is currently acting more like an aggregate data-reporting/policy/UI flag than a direct crash-submission implementation flag.

## Current risk assessment

Measured Veil runtime artifacts now show:

- no persistent telemetry/data-reporting identifiers in a clean profile
- no clean-profile `toolkit.telemetry.previousBuildID`
- no clean-profile Push identifier or Push startup socket
- no `datareporting.policy.*` entries in built `greprefs.js`
- no data-reporting upload or policy prefs serialized into Veil-generated backups after `VEIL-0206`

What remains is compile-time and policy-surface hygiene:

- `AppConstants.MOZ_DATA_REPORTING === true`
- `TelemetryReportingPolicy` and adjacent helpers still compile
- backup manifest metadata still carries some telemetry/reporting-adjacent fields in a user-initiated path
- the preferences data-collection section is still partly gated by `MOZ_DATA_REPORTING` because the crash-reporting checkbox lives there

Forcing `MOZ_DATA_REPORTING` off immediately would go further than the current measured problem justifies. After `VEIL-0205`, the default-pref residue is gone from built `greprefs.js`, the clean-profile runtime artifact still shows no data-reporting state generation, and the remaining caveat is mostly aggregate compile-time truth-in-labeling plus a small number of deferred crashreporter-adjacent surfaces.

## Recommendation

Do not force `MOZ_DATA_REPORTING` off yet.

The next realistic paths are:

1. Audit the remaining crashreporter-adjacent backup/profile surfaces before touching the aggregate configure relationship.
2. Separate crashreporter from the aggregate `MOZ_DATA_REPORTING` configure relationship only if that audit shows a clean, maintainable split.

Until then, `MOZ_DATA_REPORTING` should be treated as Veil's last major compile-time telemetry/data-reporting caveat, not as evidence of active clean-profile telemetry behavior in the current measured build.
