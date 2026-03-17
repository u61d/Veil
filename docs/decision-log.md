# Veil Decision Log

## D-0001: Use a patch-managed fork repo first

- Date: `2026-03-14`
- Decision: Keep Veil as a patch-managed repository that targets an upstream Firefox checkout instead of importing the full Firefox source tree into this repo on day one.
- Why: The workspace started empty. A patch queue plus automation keeps the initial change set reviewable and makes future rebases easier to reason about.
- Consequence: Veil must maintain strong bootstrap and patch-application scripts, and eventually test against a full upstream checkout in CI.

## D-0002: Treat privacy and anonymity as separate product claims

- Date: `2026-03-14`
- Decision: Veil will position itself as privacy-first and hardened, not anonymous by default.
- Why: Telemetry removal and lower background traffic do not provide Tor Browser threat model guarantees, and careless hardening can increase fingerprint uniqueness.
- Consequence: Marketing and documentation must avoid overclaiming.

## D-0003: Use a layered telemetry disable strategy

- Date: `2026-03-14`
- Decision: Veil will disable telemetry and related study mechanisms in layers:
  - compile-time when supportable
  - runtime prefs where needed
  - UI cleanup where appropriate
  - tests and assertions for regression protection
- Why: Firefox has separate build flags, prefs, and startup services. Only turning off one upload switch is not enough.
- Consequence: The audit matrix distinguishes collection, upload, and service initialization.

## D-0004: Do not disable security-sensitive network services without replacement

- Date: `2026-03-14`
- Decision: Safe Browsing, updates, and similar security-linked services are not being disabled in the first Veil patch set.
- Why: Reducing background requests is not a valid reason to silently weaken security posture.
- Consequence: These services stay in the network matrix as dangerous to disable without replacement and need explicit later design work.

## D-0005: Start with upstream-supported default pref changes

- Date: `2026-03-14`
- Decision: The first authored Veil patches only touch documented default-pref surfaces already present in upstream source.
- Why: This gives Veil immediate privacy value without introducing large, fragile source divergence.
- Consequence: Compile-time disables, deeper UI removal, and build branding follow after the baseline patch queue is proven.

## D-0006: Prefer pinned source archives over blobless partial clones in unstable network environments

- Date: `2026-03-14`
- Decision: Veil's bootstrap path now defaults to a pinned GitHub codeload archive for the current branch head, with git checkout kept as an explicit alternate method.
- Why: The previously tested blobless partial clone deferred network access into checkout and failed when a promised blob fetch hit DNS resolution problems. The pinned archive path completed reliably in the same environment.
- Consequence: The default bootstrap path yields a usable source tree with exact revision metadata, but not a full upstream history checkout. Git-based maintenance workflows remain available as an alternate path when the environment supports them reliably.

## D-0007: Split compile-time telemetry gating by configure mechanism

- Date: `2026-03-14`
- Decision: `MOZ_SERVICES_HEALTHREPORT` and `MOZ_NORMANDY` are disabled by patching `browser/moz.configure`, while `MOZ_TELEMETRY_REPORTING` is disabled in a Veil-specific mozconfig.
- Why: Current upstream configure semantics make `MOZ_SERVICES_HEALTHREPORT` and `MOZ_NORMANDY` project flags that are only settable via `imply_option`, but `MOZ_TELEMETRY_REPORTING` remains a mozconfig/env option.
- Consequence: `VEIL-0100` remains narrow and aligned with upstream configure behavior, while `MOZ_DATA_REPORTING` still requires explicit caveat handling because crashreporter can keep it defined.

## D-0008: Carry the glslopt Linux build fix as a path-patched third-party crate

- Date: `2026-03-14`
- Decision: Veil carries the current `glslopt` Linux compatibility workaround by adding a `[patch.crates-io]` override for `glslopt` and patching the local vendored crate, rather than editing the vendored source without changing Cargo resolution.
- Why: Cargo checksum enforcement rejects in-place edits to registry crates. The path override makes the workaround explicit, reproducible, and patch-queue-friendly.
- Consequence: Veil's build queue now includes a build-compat patch (`VEIL-0150`) that is separate from privacy or telemetry behavior changes.

## D-0009: Treat the Clang 21 negation-conversion warning as a build-environment workaround for now

- Date: `2026-03-14`
- Decision: The current Linux build attempt adds `-Wno-error=implicit-int-conversion-on-negation` through `CFLAGS` and `CXXFLAGS` instead of landing a source patch for the generated Servo style-constant warning immediately.
- Why: The warning originates from current host compiler behavior against generated headers, and the critical path is to get a measurable Veil build rather than widen the fork with toolchain-specific source edits prematurely.
- Consequence: Current build instructions must include the extra compiler flags, and Veil should remove this workaround once upstream or a narrowly justified source fix is available.

## D-0010: Patch the geckolib cbindgen template once the compiler-flag workaround proved insufficient

- Date: `2026-03-14`
- Decision: Veil carries a narrow source patch in `servo/ports/geckolib/cbindgen.toml` to emit an explicit signed cast for `ShadowCascadeOrder()`.
- Why: The actual `DrawTargetWebgl.cpp` compile still failed because Firefox also passes `-Werror=implicit-int-conversion`, which overrode the narrower `-Wno-error=implicit-int-conversion-on-negation` workaround. The generator template is the smallest upstream-owned source that produces the failing line.
- Consequence: Veil's Linux build queue now includes `VEIL-0160`. The extra compiler flag remains in the current build instructions until the full build path is proven cleanly.

## D-0011: Attribute startup traffic with both packets and process sockets

- Date: `2026-03-14`
- Decision: Veil's first startup network audit uses `tshark` packet capture plus repeated `lsof -p <browser-pid> -i` snapshots.
- Why: This environment has ambient background traffic on the capture interfaces, so packet capture alone would over-attribute unrelated traffic to the browser.
- Consequence: `scripts/audit_network_baseline.py` records both raw packets and browser PID socket observations, and the resulting audit docs must distinguish direct browser attribution from interface-level observations.

## D-0012: Do not claim zero telemetry until local state generation is removed

- Date: `2026-03-14`
- Decision: Veil will not claim zero telemetry for Alpha while clean-profile startup still creates telemetry-, data-reporting-, and Nimbus-related identifiers locally.
- Why: Upload suppression and build-flag gating are not enough if the browser still generates `toolkit.telemetry.cachedClientID`, `datareporting/state.json` IDs, and `nimbus.profileId` on startup.
- Consequence: The next telemetry phase must target local ID/state creation and not just upload endpoints.

## D-0013: Do not persist reporting identifiers when both upload channels are off

- Date: `2026-03-14`
- Decision: Veil suppresses persistent `ClientID.sys.mjs` state when both `datareporting.healthreport.uploadEnabled` and `datareporting.usage.uploadEnabled` are false.
- Why: Clean-profile startup was still creating stable telemetry- and data-reporting-related identifiers locally even after compile-time and upload-surface reductions.
- Consequence: Veil now keeps canary identifiers in memory for callers that still expect an ID-shaped value, clears stale cached prefs and `datareporting/state.json`, and no longer writes those stable IDs in the default-off case.

## D-0014: Remove Nimbus profile-ID import side effects before considering broader Nimbus removal

- Date: `2026-03-14`
- Decision: Veil makes `nimbus.profileId` lazy instead of generating it during `ExperimentAPI` construction.
- Why: `MOZ_NORMANDY` startup removal did not eliminate `nimbus.profileId` writes; the immediate source was a persistent pref side effect during module initialization.
- Consequence: Clean-profile startup no longer writes `nimbus.profileId`, while Nimbus source stays compiled and future product decisions can still remove or defer more of the subsystem if justified.

## D-0015: Default off first-run reporting-policy fetches, region lookup, and connectivity checks

- Date: `2026-03-14`
- Decision: Veil defaults `datareporting.policy.firstRunURL` to empty, bypasses the reporting-policy notification, disables startup region lookup, and disables captive-portal/connectivity checks.
- Why: These startup requests were source-traced, not security-essential for basic browser startup, and produced avoidable unsolicited network traffic in a clean profile.
- Consequence: `www.mozilla.org`, `location.services.mozilla.com`, and `detectportal.firefox.com` are gone from the reduced startup audit, but Veil must document the UX tradeoffs around captive-portal detection and region-based defaults.

## D-0016: Suppress previous-build telemetry metadata when reporting uploads are off

- Date: `2026-03-14`
- Decision: Veil clears and does not persist `toolkit.telemetry.previousBuildID` when both reporting upload prefs are disabled.
- Why: The pref was still being written on clean-profile startup, and current source ties it to telemetry metadata rather than to core upgrade behavior.
- Consequence: Clean-profile startup no longer writes `toolkit.telemetry.previousBuildID`; if a user later re-enables reporting uploads, the next run behaves like a first reporting run for build-ID metadata.

## D-0017: Defer Push startup on clean profiles instead of disabling Push globally

- Date: `2026-03-14`
- Decision: Veil keeps Push available but stops auto-initializing it on clean-profile startup unless the profile already has persisted push state that needs background delivery.
- Why: Unconditional `PushService.ensureReady` created `dom.push.userAgentID` and a `push.services.mozilla.com` connection on every clean startup. A deferral strategy preserves existing subscribed profiles better than globally defaulting Push off.
- Consequence: Clean-profile startup no longer generates Push identifiers or sockets, while existing profiles with persisted PushDB records or broadcast listeners still initialize Push automatically.

## D-0018: Treat PushDB as the authoritative startup state signal, not a bare UAID

- Date: `2026-03-14`
- Decision: Veil now probes PushDB and broadcast-listener state before auto-starting Push, and no longer treats a bare `dom.push.userAgentID` pref as sufficient startup state.
- Why: Real subscriptions are stored in PushDB. A bare UAID can outlive actual subscriptions and would reintroduce unsolicited startup traffic without proving any legitimate background delivery need.
- Consequence: Clean profiles and stale-UAID profiles stay quiet, while seeded persisted subscription state still reactivates startup Push initialization.

## D-0019: Remove data-reporting UI surfaces before attempting macro surgery

- Date: `2026-03-14`
- Decision: Veil removes the data-submission infobar startup hooks and the telemetry/upload/studies/addon-recommendation controls from the preferences UI while leaving crashreporter controls separate.
- Why: These were reachable `MOZ_DATA_REPORTING`-gated surfaces that no longer matched Veil product behavior, and they can be removed safely without changing crashreporter internals.
- Consequence: The remaining `MOZ_DATA_REPORTING` caveat is now narrower: compile-time aggregate state plus `datareporting.policy.*` pref residue, not active reporting UI on a finished Veil build.

## D-0020: Validate Push deferral with upstream Push tests before changing behavior further

- Date: `2026-03-15`
- Decision: Veil uses the upstream `dom/push/test/mochitest.toml` suite as the primary correctness check for `VEIL-0203`, instead of relying on synthetic PushDB seeding alone.
- Why: Synthetic persisted-state seeding was enough to prove startup reactivation, but it was not a faithful substitute for real service-worker permission and subscription flows.
- Consequence: Veil can now treat the earlier seeded-profile errors as a harness limitation and keep the current Push deferral behavior without broadening the change.

## D-0021: Remove remaining data-reporting residue by narrowing pref surfaces, not by forcing `MOZ_DATA_REPORTING` off

- Date: `2026-03-15`
- Decision: Veil removes `datareporting.policy.*` built defaults and adjacent pref-plumbing surfaces while leaving the crashreporter-linked `MOZ_DATA_REPORTING` aggregate untouched.
- Why: The measured clean-profile runtime no longer shows active data-reporting state generation, so the highest-value remaining work is to reduce reachable policy residue without risking crash handling.
- Consequence: `datareporting.policy.*` is now absent from built `greprefs.js`, cross-profile/message surfaces are smaller, and `MOZ_DATA_REPORTING` remains an explicit compile-time caveat rather than an immediate removal target.

## D-0022: Neutralize backup serialization before attempting any aggregate split

- Date: `2026-03-15`
- Decision: Veil removes data-reporting upload prefs, policy state, and cached usage-profile identifiers from Veil-generated backup exports, while leaving crash auto-submit and backup schema behavior untouched.
- Why: Backup export is one of the few remaining user-initiated runtime paths that could still serialize data-reporting state even after clean-profile startup had been hardened.
- Consequence: New Veil backups no longer carry those pref surfaces by default, and the remaining `MOZ_DATA_REPORTING` caveat is narrower still: compile-time aggregate state plus a small set of deferred backup-schema and crash-UI surfaces.

## D-0023: Rebrand the local Linux runtime by replacing upstream unofficial branding in place

- Date: `2026-03-15`
- Decision: Veil reuses the upstream `browser/branding/unofficial` bundle as its Linux branding base, but replaces the display name, localized brand strings, wordmarks, logo SVG, and update URLs with Veil-owned values.
- Why: The current Alpha build was still presenting itself as Nightly in user-visible Linux runtime surfaces, which is both confusing for local use and out of scope with Veil's own product identity.
- Consequence: The current Linux runtime can present itself as Veil without introducing a large new branding directory or a separate asset pipeline before the rest of the packaging work is ready.

## D-0024: Remove inactive Mozilla promo panes instead of leaving them to fail at runtime

- Date: `2026-03-15`
- Decision: Veil disables the More From Mozilla preferences pane and removes Quick Suggest from idle startup rather than leaving those upstream surfaces loaded but mostly off.
- Why: With region lookup already disabled, `moreFromMozilla.js` was still assuming `Region.home` existed, and Quick Suggest was still idle-starting even though Veil leaves the feature off by default.
- Consequence: Clean Linux runtime logs are quieter, the preferences UI no longer exposes leftover Mozilla promo content, and core search remains intact because the Quick Suggest modules stay available for explicit settings code paths instead of startup initialization.

## D-0025: Use Linux launcher-level remoting-name override while clean reconfigure remains blocked

- Date: `2026-03-15`
- Decision: Veil's local Linux launcher exports `MOZ_APP_REMOTINGNAME=veil`, and the desktop entry uses `StartupWMClass=veil`.
- Why: The current workspace still cannot complete a clean reconfigure because the staged clang toolchain is missing the WASI builtins archive needed by Firefox's wasm linker probe, so generated runtime metadata still carries upstream app identifiers.
- Consequence: Local Linux menu and window-class matching can use `veil` immediately, while the remaining `Firefox` and `Nightly` compiled identifiers stay documented as a build-environment blocker rather than being hidden or misrepresented.

## D-0026: Fix the Arch Linux WASI blocker in the local build wrapper instead of mutating the host toolchain

- Date: `2026-03-15`
- Decision: Veil's Linux rebuild script overlays a local clang resource dir and supplies a usable WASI builtins archive there, instead of requiring the workspace host to install or replace Arch system toolchain packages before Veil can build.
- Why: The actual missing artifact was the Arch `wasi-compiler-rt` package payload, but Veil needs a reproducible workspace-local fix that does not depend on mutating the host package set.
- Consequence: `./scripts/rebuild_veil_linux_clean.sh` can clobber and rebuild Veil successfully in the current workspace, and the generated runtime identity now reflects Veil instead of upstream Nightly branding.

## D-0027: Rebrand only the remaining visible Home, New Tab, and Labs surfaces after the clean rebuild

- Date: `2026-03-15`
- Decision: Veil patches the exact locale and settings-configuration owners for `Firefox Home`, the Home sponsor mission copy, and the visible `Firefox Labs` label instead of continuing with broad string replacement.
- Why: After the clean rebuild fixed generated `application.ini` identity, the remaining user-facing Firefox branding was limited to a short list of concrete Home/New Tab/Settings surfaces that could be traced and verified directly from the packaged runtime.
- Consequence: The Linux build now presents `Veil Home`, `Veil Labs`, and neutral sponsored-content wording in the packaged runtime without changing the underlying Home/New Tab feature set.

## D-0028: Treat the Applications default-handler label as desktop integration, not a Veil branding string

- Date: `2026-03-16`
- Decision: Veil does not patch the `Use Firefox (default)` label in Applications settings at the source level.
- Why: The label comes from the host desktop default-handler description, not from a Firefox-owned branding string. With a temporary `veil.desktop` mailto default, the same Settings UI shows `Use Veil (default)` without any source change.
- Consequence: Linux packaging and local desktop registration need to install a real `veil.desktop` handler before that Settings row will reflect Veil on user systems.

## D-0029: Hide Firefox-specific Settings integrations that do not map to Veil services

- Date: `2026-03-16`
- Decision: Veil hides the Firefox Relay checkbox by default and removes the Sync page's Firefox mobile download promo instead of renaming those Mozilla services.
- Why: `Firefox Relay` is a real Mozilla service name and would be inaccurate if rebranded. The Android/iOS promo explicitly advertises Firefox mobile products, which Veil does not ship.
- Consequence: The visible Settings UI no longer suggests a Veil-branded Relay service or promotes Firefox mobile downloads, while core Sync and password behavior stay intact.
