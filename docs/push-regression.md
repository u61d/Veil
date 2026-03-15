# Veil Push Regression Note

Status date: `2026-03-15`

This note records what Veil has verified about Push behavior after `VEIL-0203`.

## Source ownership

Startup ownership remains:

- `browser/components/BrowserGlue.sys.mjs`
- `dom/push/PushComponents.sys.mjs`
- `dom/push/PushService.sys.mjs`
- `dom/push/PushServiceWebSocket.sys.mjs`

The current startup path is:

1. `BrowserGlue` schedules `PushService.ensureReady`.
2. Veil routes that through `PushComponents.maybeEnsureReady()`.
3. `maybeEnsureReady()` now auto-initializes only when persisted Push state exists.
4. First real `Push.subscribe()` use still goes through the normal on-demand registration path.

## Exact startup conditions after `VEIL-0203`

On browser startup, Veil auto-initializes Push only when at least one of these is true:

1. `broadcast-listeners.json` contains persisted listeners.
2. PushDB contains persisted subscription records.

If neither state source exists:

- clean-profile startup stays deferred
- a bare stale `dom.push.userAgentID` pref is cleared instead of being treated as sufficient startup state

## Scenarios checked

### 1. Clean-profile startup

- Artifact: `/home/null2ud/Projects/Veil/artifacts/network-audit/after-20260315-mozdata/summary.json`
- Result:
  - `push.services.mozilla.com` absent from `lsof_remote_endpoints`
  - `dom.push.userAgentID` absent from the profile artifact
  - only the retained security-sensitive Remote Settings/content-signature endpoints remain browser-attributed

### 2. Seeded subscribed-profile startup

- Seed method:
  - `scripts/seed_push_profile.py --mode subscription`
  - creates a real PushDB record under `storage/permanent/chrome/idb/2918063365piupsah.sqlite`
  - does not preseed `dom.push.userAgentID`
- Seeded profile:
  - `/home/null2ud/Projects/Veil/artifacts/push-profiles/subscribed-profile-no-uaid`
- Audit artifact:
  - `/home/null2ud/Projects/Veil/artifacts/network-audit/after-20260314-push-subscribed/summary.json`
- Result:
  - `push.services.mozilla.com` reappears on startup
  - clean-profile-only suppression remains intact for profiles without PushDB or broadcast-listener state

### 3. Real subscribed-site Push behavior

This run used the upstream-controlled Push mochitest suite instead of synthetic DB state alone.

- Runner:
  - `/home/null2ud/Projects/Veil/scripts/run_push_regression.py`
- Invocation:
  - `../mach python --exec-file /home/null2ud/Projects/Veil/scripts/run_push_regression.py -- --artifact-dir /home/null2ud/Projects/Veil/artifacts/push-mochitest/20260315`
- Harness setup:
  - packaged mochitest harness from `obj-veil/_tests/testing/mochitest`
  - symlinked Push test subtree so the packaged harness can run `dom/push/test/mochitest.toml`
- Primary artifacts:
  - `/home/null2ud/Projects/Veil/artifacts/push-mochitest/20260315/dom_push_suite.raw.log`
  - `/home/null2ud/Projects/Veil/artifacts/push-mochitest/20260315/dom_push_suite.mach.log`

Suite result:

- `mochitest-plain`
- `Ran 173 checks (159 subtests, 14 tests)`
- `Unexpected results: 0`

Representative end-to-end checks that passed:

- `dom/push/test/test_register.html`
  - permission grant
  - subscribe
  - worker resubscribe endpoint stability
  - unsubscribe
- `dom/push/test/test_subscription_change.html`
  - create subscription
  - revoke permission
  - `getSubscription()` returns `null`
  - drop subscription after permission reinstatement
- `dom/push/test/test_data.html`
  - endpoint validation
  - `p256dh` key material
  - auth secret

## Conclusion

Conclusion: `preserved`

`VEIL-0203` preserves legitimate Push behavior in the strongest controlled local harness available in this environment:

- clean profiles stay quiet
- profiles with persisted subscription state re-enable startup Push
- real service-worker Push subscription flows still pass in the upstream mochitest suite

## What the earlier seeded-profile errors now mean

The earlier seeded subscribed-profile run logged:

- `NS_ERROR_FAILURE ... [nsIPushNotifier.notifySubscriptionChange]`
- `AbortError`

That is now best classified as a synthetic-profile limitation, not a proven Veil Push regression. The seeded record was sufficient to prove startup reactivation, but not sufficient to recreate the full service-worker, permission, and origin context that the upstream mochitests exercise directly.

## Remaining limitation

This run did not use an external public push service. The strongest reproducible proof available here is the upstream in-tree Push mochitest suite, which covers real service-worker subscription behavior and related Push flows under Mozilla's own local test harness.
