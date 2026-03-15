# Veil Vision

## Mission

Build Veil as a serious, maintainable Firefox-based browser fork with:

- zero product telemetry by default
- minimal unsolicited network communication
- strong privacy defaults
- conservative anti-fingerprinting where it reduces uniqueness instead of increasing it
- clean redistribution branding that does not depend on Mozilla or Firefox trademarks
- reproducible maintenance, testing, and rebase workflow

## Product principles

1. Stay close enough to upstream Firefox that security rebases remain realistic.
2. Prefer upstream-supported build flags and default-pref changes over deep invasive rewrites.
3. Separate privacy claims from anonymity claims.
4. Prefer reduced uniqueness over a long list of niche toggles.
5. Do not remove security features just because they create network traffic.
6. Every claim must be testable or tightly qualified.

## Veil Alpha 1 scope

Veil Alpha 1 should deliver:

- a documented patch-managed Firefox fork workflow
- Veil branding placeholders and redistribution rules
- telemetry disabled by default through runtime prefs first, compile-time flags next
- first-pass suppression of low-risk unsolicited Mozilla service traffic
- written threat model and audit matrices
- static verification of the initial source assertions

## Feature and claim boundary

| Claim | Veil position |
| --- | --- |
| Private browser | Yes, this is a core goal. |
| Hardened browser | Yes, within compatibility and maintainability bounds. |
| Anti-fingerprinting browser | Partial and conservative only. |
| Anonymity browser | No, not by default. |
| Tor replacement | No. |

## Definition of done

### Zero telemetry

Zero telemetry is done when:

- known desktop telemetry, usage reporting, study enrollment, and related upload paths are enumerated
- collection and upload are both addressed where practical
- compile-time disables are used where supportable
- runtime defaults and UI affordances are aligned with the claim
- verification proves the relevant prefs and services are off in a clean profile
- the claim document states what is excluded, such as crash reporting if still user-opt-in

### Minimal unsolicited network activity

This is done when:

- clean-profile browser-initiated traffic is captured before and after changes
- every request source is mapped to a module, pref, or service
- each behavior is categorized as must remove, optional default-off, necessary, or dangerous to disable without replacement
- the rationale is documented with compatibility and security notes

### Privacy-first release candidate

This is done when:

- default pref changes are documented with old value, new value, reason, compatibility risk, and fingerprinting impact
- privacy improvements do not create obviously unique browser behavior without justification
- verification and regression checks are part of the routine release process
