# Veil Alpha Release Verification

Status date: `2026-03-15`

This note records what was rechecked before the GitHub Alpha decision.

## Fresh source and replay

- Fresh source extraction from `upstream/firefox-16a7dee3ca6fb0967cd84314393ad1d2e213e4a6.tar.gz`: yes
- Full Veil patch replay on that fresh tree: pass
- Fresh Veil configure on that fresh tree: fail in this workspace

Current configure failure:

- `wasm-ld: error: cannot open /usr/lib/clang/22/lib/wasm32-unknown-wasi/libclang_rt.builtins.a`

Meaning:

- The current patch queue still reapplies cleanly.
- The current staged toolchain recipe is not enough to claim a clean fresh configure in this workspace today.
- Runtime verification below was therefore performed against the existing built Veil runtime at `upstream/firefox-16a7dee3ca6fb0967cd84314393ad1d2e213e4a6/obj-veil`.

## Veil runtime recheck

Artifact bundle:

- `artifacts/alpha-readiness/20260315T145947Z`

Results:

- runtime verifier: `pass`, `0` failures, `2` warnings
- backup-surface verifier: `pass`, `0` failures
- clean-profile startup audit: `datareporting/state.json` absent
- retained Mozilla startup hosts:
  - `firefox.settings.services.mozilla.com`
  - `firefox-settings-attachments.cdn.mozilla.net`
  - `content-signature-2.cdn.mozilla.net`

Manual profile and log checks:

- no `toolkit.telemetry.cachedClientID` in the clean Veil `prefs.js`
- no `toolkit.telemetry.cachedProfileGroupID` in the clean Veil `prefs.js`
- no `nimbus.profileId` in the clean Veil `prefs.js`
- no `dom.push.userAgentID` in the clean Veil `prefs.js`
- `artifacts/alpha-readiness/20260315T145947Z/network-audit/profile/datareporting/state.json`: absent

## Upstream comparison

Exact same-revision runtime comparison was not completed because the fresh upstream configure/build path was not reproduced in this workspace.

What was compared instead:

1. Same-revision source comparison against the clean upstream tarball
2. Runtime comparison against local stock Firefox `148.0.2` as a non-equivalent sanity baseline

### Same-revision source comparison

Relative to the clean upstream tarball, Veil changes the verified defaults for:

- `datareporting.healthreport.uploadEnabled`
- `datareporting.usage.uploadEnabled`
- `datareporting.policy.dataSubmissionEnabled`
- `datareporting.policy.firstRunURL`
- `toolkit.telemetry.*` startup ping prefs
- `browser.region.network.url`
- `network.connectivity-service.enabled`
- `network.captive-portal-service.enabled`
- `app.shield.optoutstudies.enabled`
- `app.normandy.api_url`
- `browser.discovery.enabled`
- `browser.topsites.contile.enabled`
- `browser.newtab.preload`

The built Veil package also removes the telemetry/studies controls from `about:preferences` while keeping the crash auto-submit control.

### Runtime comparison against stock Firefox on this machine

Stock Firefox audit artifact:

- `artifacts/release-verify/upstream-system-firefox-audit`

Observed stock Firefox clean-profile startup state that Veil no longer creates:

- `toolkit.telemetry.cachedClientID`
- `toolkit.telemetry.cachedProfileGroupID`
- `toolkit.telemetry.previousBuildID`
- `datareporting.dau.cachedUsageProfileID`
- `datareporting.dau.cachedUsageProfileGroupID`
- `datareporting.policy.dataSubmissionPolicyAcceptedVersion`
- `datareporting.policy.dataSubmissionPolicyNotifiedTime`
- `nimbus.profileId`
- `dom.push.userAgentID`
- `datareporting/state.json`

Observed stock Firefox startup hosts beyond Veil's retained set:

- `location.services.mozilla.com`
- `detectportal.firefox.com`
- `push.services.mozilla.com`
- `incoming.telemetry.mozilla.org`
- `normandy.cdn.mozilla.net`
- `merino.services.mozilla.com`
- `classify-client.services.mozilla.com`
- `www.mozilla.org`
- `archive.mozilla.org`
- `ads.mozilla.org`

This comparison is useful, but it is not the same as a same-revision upstream runtime build.

## Smoke tests

Artifact:

- `artifacts/release-verify/veil-smoke-20260315-release.json`

Current results:

- pass: first launch
- pass: local page load
- pass: multiple tabs
- pass: download
- pass: settings page load with current crash/telemetry UI boundaries
- pass: service worker registration
- pass: temporary extension install
- pass: private-window launch
- warn: interactive search UI not verified in this headless harness

The same headless `about:home` / `about:newtab` search-input check also came back empty in stock Firefox on this machine, so this warning is currently treated as a harness limit, not a proven Veil regression.

## Push

Current Push regression artifact:

- `artifacts/release-verify/push-mochitest-20260315`

Result:

- upstream `dom/push` mochitest suite passed against the current Veil build

Release-pass note:

- A same-day rerun attempt in this workspace hit local Python harness dependency issues before the browser test phase.
- No browser-side Push changes landed after the recorded passing artifact above.
- The Push conclusion for this release therefore still rests on the existing same-day passing artifact.

## Release conclusion

Veil is good enough for a restrained GitHub Alpha release if the wording stays narrow.

It is not good enough for:

- a "zero telemetry" claim
- a "zero network traffic" claim
- a fresh-build reproducibility claim in this workspace
- a broad, unqualified "all core functionality verified" claim
