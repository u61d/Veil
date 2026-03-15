# Firefox Architecture Map For Veil

This memo maps the current upstream areas Veil needs to control first.

## Build and product configuration

| Area | Upstream path | Veil relevance |
| --- | --- | --- |
| Bootstrap entry point | `python/mozboot/bin/bootstrap.py` | Official script for creating a Firefox development checkout; points Git users at the Firefox Git mirror. |
| Build configuration | `toolkit/moz.configure` | Defines `MOZ_TELEMETRY_REPORTING`, `MOZ_SERVICES_HEALTHREPORT`, `MOZ_NORMANDY`, and derived `MOZ_DATA_REPORTING`. |
| Unofficial branding | `browser/branding/unofficial/` | Baseline for non-Mozilla redistribution; Veil should not ship official Firefox branding. |

## Runtime defaults and pref surfaces

| Area | Upstream path | Key prefs or behavior |
| --- | --- | --- |
| Browser defaults | `browser/app/profile/firefox.js` | Telemetry ping prefs, Normandy URL, discovery, Contile, New Tab behavior, Sync-related prefs. |
| Global static prefs | `modules/libpref/init/StaticPrefList.yaml` | Static defaults for `datareporting.*`, partitioning, and resist-fingerprinting prefs. |
| Global default prefs | `modules/libpref/init/all.js` | Search suggestions, geolocation network URL, connectivity service, captive portal URL, region update, DNS prefetch, speculative network behavior. |

## Telemetry and studies

| Area | Upstream path | Veil relevance |
| --- | --- | --- |
| Core telemetry controller | `toolkit/components/telemetry/app/TelemetryController.sys.mjs` | Main telemetry orchestration path; needs compile-time and runtime review. |
| Usage reporting bridge | `toolkit/components/telemetry/app/UsageReporting.sys.mjs` | Maps general data-reporting pref to usage upload behavior. |
| Telemetry docs | `toolkit/components/telemetry/` | Upstream component documentation and implementation context. |
| Nimbus experiment API | `toolkit/components/nimbus/ExperimentAPI.sys.mjs` | Studies depend on both pref state and telemetry enablement. |
| Remote Settings experiment loader | `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs` | Timer-driven recipe updates and Remote Settings-backed experiment fetch path. |

## Browser startup and unsolicited network triggers

| Area | Upstream path | Observed relevance |
| --- | --- | --- |
| Startup coordinator | `browser/components/BrowserGlue.sys.mjs` | Schedules Push initialization, discovery update, Remote Settings init, search background checks, and background update work. |
| Push persistence | `dom/push/PushDB.sys.mjs`, `dom/push/PushBroadcastService.sys.mjs` | Real persisted Push startup state lives in PushDB and `broadcast-listeners.json`, not just in `dom.push.userAgentID`. |
| Remote Settings | `services/settings/remote-settings.sys.mjs` | Polling, bundle extraction, collection sync, and associated telemetry. |
| Enterprise policy controls | `browser/components/enterprisepolicies/Policies.sys.mjs` | Existing upstream controls for telemetry, studies, and updates; useful precedent for Veil behavior and tests. |
| Automation baseline prefs | `remote/shared/RecommendedPreferences.sys.mjs` | Upstream no-network pref set used by automation; useful comparison point for Veil audits. |

## Security and privacy-sensitive services

| Area | Upstream path | Veil note |
| --- | --- | --- |
| Safe Browsing | `toolkit/components/url-classifier/` and related prefs in `modules/libpref/init/all.js` | Security-sensitive; do not disable casually. |
| Captive portal detection | `toolkit/components/captivedetect/` and `captivedetect.*` prefs in `modules/libpref/init/all.js` | Candidate for default-off depending on product decision and UX replacement. |
| Geolocation provider | `geo.provider.network.url` in `modules/libpref/init/all.js` and geolocation service code | Network-privacy sensitive; likely default-off unless a replacement exists. |
| App updates | `toolkit/mozapps/update/` and `app.update.*` prefs | Security-sensitive; needs replacement strategy if Veil wants less vendor coupling. |
| New Tab and recommendations | `browser/components/newtab/` and related prefs in `browser/app/profile/firefox.js` | High-value area for unsolicited requests and telemetry-adjacent traffic. |

## Key build flags and prefs to track

- Build flags:
  - `MOZ_TELEMETRY_REPORTING`
  - `MOZ_SERVICES_HEALTHREPORT`
  - `MOZ_NORMANDY`
  - `MOZ_DATA_REPORTING`
  - `MOZ_UPDATER`
- Telemetry and study prefs:
  - `datareporting.healthreport.uploadEnabled`
  - `datareporting.usage.uploadEnabled`
  - `toolkit.telemetry.archive.enabled`
  - `toolkit.telemetry.shutdownPingSender.enabled`
  - `toolkit.telemetry.firstShutdownPing.enabled`
  - `toolkit.telemetry.newProfilePing.enabled`
  - `toolkit.telemetry.updatePing.enabled`
  - `toolkit.telemetry.bhrPing.enabled`
  - `app.shield.optoutstudies.enabled`
  - `app.normandy.api_url`
- Network/privacy prefs:
  - `browser.discovery.enabled`
  - `browser.topsites.contile.enabled`
  - `browser.newtab.preload`
  - `browser.search.suggest.enabled`
  - `browser.urlbar.suggest.searches`
  - `browser.region.update.enabled`
  - `geo.provider.network.url`
  - `network.connectivity-service.enabled`
  - `captivedetect.canonicalURL`
  - `privacy.partition.network_state`
  - `privacy.resistFingerprinting`
  - `privacy.resistFingerprinting.pbmode`

## Compile-time vs runtime note

- Compile-time coverage in Veil currently maps to:
  - `browser/moz.configure` for product-implied project flags such as `MOZ_SERVICES_HEALTHREPORT` and `MOZ_NORMANDY`
  - Veil mozconfig for `MOZ_TELEMETRY_REPORTING`
- Current configure-backed evidence lives in `obj-veil/config.status.json`, which records the Veil mozconfig, `MOZ_TELEMETRY_REPORTING=`, and the resulting compile-time option set for the current Linux build attempt.
- `scripts/verify_telemetry_runtime.py` now automates those objdir assertions and explicitly records the current `MOZ_DATA_REPORTING` caveat.
- `docs/moz_data_reporting-dependency-map.md` records the current source-backed scope of `MOZ_DATA_REPORTING` and why crashreporter is the remaining input keeping it enabled in Veil's build.
- Current upstream nuance: `MOZ_NORMANDY` does not prevent `toolkit/components/nimbus` from compiling. The flag is still meaningful because it gates browser startup registration in `browser/components/BrowserComponents.manifest` and related UI/runtime surfaces.
- Runtime coverage remains necessary because:
  - some ping prefs are independent of compile-time gating
  - `MOZ_DATA_REPORTING` can still remain on if crashreporter remains enabled
  - UI and service behavior must still be verified from a built binary
