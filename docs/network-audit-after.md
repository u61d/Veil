# Veil Startup Network Audit After

Status date: `2026-03-14`

## Method

- Browser: `/home/null2ud/Projects/Veil/upstream/firefox/obj-veil/dist/bin/firefox`
- Run mode: `--headless --no-remote --profile <fresh-profile> about:blank`
- Duration: 20 seconds
- Capture method:
  - `tshark` on interface `any`
  - repeated `lsof -p <browser-pid> -i` snapshots for browser-owned socket attribution
- Artifacts:
  - Baseline after the first Veil build:
    - `/home/null2ud/Projects/Veil/artifacts/network-audit/after-20260314/summary.json`
  - Reduced startup run after the current suppression work:
    - `/home/null2ud/Projects/Veil/artifacts/network-audit/after-20260314-reduction4/startup.pcapng`
    - `/home/null2ud/Projects/Veil/artifacts/network-audit/after-20260314-reduction4/startup-packets.tsv`
    - `/home/null2ud/Projects/Veil/artifacts/network-audit/after-20260314-reduction4/browser-sockets.log`
    - `/home/null2ud/Projects/Veil/artifacts/network-audit/after-20260314-reduction4/summary.json`
  - Seeded subscribed-profile Push regression run:
    - `/home/null2ud/Projects/Veil/artifacts/push-profiles/subscribed-profile-no-uaid`
    - `/home/null2ud/Projects/Veil/artifacts/network-audit/after-20260314-push-subscribed/summary.json`

## Before and after summary

| Surface | First measured Veil build | Current reduced run | Source trace / note |
| --- | --- | --- | --- |
| `toolkit.telemetry.cachedClientID` and `toolkit.telemetry.cachedProfileGroupID` | Present | Gone | `ClientID.sys.mjs` now avoids persistent ID generation when both upload prefs are false |
| `datareporting/state.json` | Present | Gone | `ClientID.sys.mjs` now clears state instead of writing stable reporting IDs in the default-off case |
| `datareporting.dau.cachedUsageProfile*` | Present | Gone | `UsageReporting.ensureInitialized()` still runs, but `ClientID.sys.mjs` keeps only in-memory canary values |
| `toolkit.telemetry.previousBuildID` | Present | Gone | `TelemetrySession.sys.mjs` no longer persists it when both reporting upload prefs are off |
| `nimbus.profileId` | Present | Gone | `ExperimentAPI.sys.mjs` no longer generates it on import alone |
| `www.mozilla.org` | Present | Gone | `BrowserGlue.sys.mjs` -> `TelemetryReportingPolicy.sys.mjs` -> `datareporting.policy.firstRunURL` |
| `location.services.mozilla.com` | Present | Gone | `Region.sys.mjs` startup region lookup via `browser.region.network.url` |
| `detectportal.firefox.com` | Present | Gone | Captive portal and connectivity checks |
| `push.services.mozilla.com` | Present | Gone on a clean profile | `BrowserGlue.sys.mjs` now defers Push startup until the profile already has broadcast listeners or persisted PushDB state |
| Remote Settings endpoints | Present | Still present | Security-sensitive; intentionally left in place in this run |
| Content-signature endpoint | Present | Still present | Security-sensitive; intentionally left in place in this run |

## Final browser-attributed remote endpoints

These endpoints come from the browser PID socket snapshots in `after-20260314-reduction4` and are therefore the strongest attribution in the reduced run.

| Endpoint | Observed host/SNI | Classification | Recommendation | Note |
| --- | --- | --- | --- | --- |
| `151.101.65.91:443` | `firefox.settings.services.mozilla.com` | 4. dangerous to disable without replacement | Keep for now; map exact Remote Settings consumers and replacement story first. | Security-sensitive Remote Settings core sync. |
| `151.101.1.91:443` | `firefox-settings-attachments.cdn.mozilla.net` | 4. dangerous to disable without replacement | Keep for now; likely attachment fetches tied to Remote Settings. | Security-sensitive or feature-coupled remote content. |
| `34.160.144.191:443` | `content-signature-2.cdn.mozilla.net` | 4. dangerous to disable without replacement | Keep for now pending signature/trust replacement design. | Security-sensitive content-signature path. |

## Source-proved startup fetch traces

- `www.mozilla.org`: `BrowserGlue.sys.mjs` startup calls `TelemetryReportingPolicy.ensureUserIsNotified()`, which can reach `_openFirstRunPage()` and open `datareporting.policy.firstRunURL`. Veil now sets that URL to `""`, disables the submission-policy prompt, and sets `toolkit.telemetry.reportingpolicy.firstRun=false`, which removed the fetch in the reduced run.
- `location.services.mozilla.com`: `Region.sys.mjs` auto-initializes at module load and fetches `browser.region.network.url` when the search region is unknown. Veil now sets `browser.region.network.url=""`, which removed the fetch in the reduced run.
- `detectportal.firefox.com`: captive portal and connectivity services own this startup traffic. Veil now sets `network.captive-portal-service.enabled=false` and `network.connectivity-service.enabled=false`, which removed the fetch in the reduced run.
- `push.services.mozilla.com`: `BrowserGlue.sys.mjs` used to schedule unconditional late-startup `PushService.ensureReady`. `PushComponents.sys.mjs` now only starts Push automatically when the profile already has broadcast listeners or persisted PushDB records. Clean-profile startup no longer reaches `push.services.mozilla.com`, while the seeded subscribed-profile artifact reintroduces the Push socket as expected.

## Local startup state in the reduced run

The reduced clean-profile run no longer creates the telemetry/data-reporting/push identifiers that were present in the earlier Veil runs.

The following items that were present in the first measured run are now absent in `after-20260314-reduction4`:

- `toolkit.telemetry.cachedClientID`
- `toolkit.telemetry.cachedProfileGroupID`
- `datareporting/state.json`
- `datareporting.dau.cachedUsageProfileID`
- `datareporting.dau.cachedUsageProfileGroupID`
- `toolkit.telemetry.previousBuildID`
- `nimbus.profileId`
- `dom.push.userAgentID`
- `datareporting.policy.dataSubmissionPolicyAcceptedVersion`
- `datareporting.policy.dataSubmissionPolicyNotifiedTime`

The only remaining `profile_pref_matches` entry in the current audit artifact is `browser.search.serpEventTelemetryCategorization.regionEnabled=false`, which is not a stable telemetry/data-reporting identifier.

## Ambient traffic note

The packet capture on `any` also saw unrelated traffic from other local processes, including ChatGPT/OpenAI, Discord, Spotify, and local discovery protocols. Those packets are not attributed to the Veil browser and should not be counted as Veil requests.
