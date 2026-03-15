# Veil Threat Model

## Intended users

Veil is for users who want:

- minimal browser phoning-home behavior
- strong privacy defaults without needing an expert hardening guide
- reduced background communication to vendor-operated services
- reduced tracking and state leakage
- some fingerprinting reduction where the tradeoffs are acceptable

## Explicit non-targets

Veil is not currently for users who need:

- strong network-layer anonymity against a powerful observer
- Tor Browser threat model guarantees
- resistance to a global passive adversary
- protection after logging into identity-rich accounts that correlate activity anyway
- a promise that fingerprinting becomes solved rather than reduced

## Attacks Veil should reduce

- passive observation of vendor background traffic from a clean profile
- default telemetry and usage reporting paths
- unwanted study enrollment or recommendation systems
- unnecessary state and metadata exposure from speculative or vendor-linked requests
- cross-site tracking mitigated by Firefox privacy features that can be enabled without making Veil unusually unique

## Attacks Veil does not solve

- IP address exposure to visited sites
- anonymity against ISPs, enterprise middleboxes, governments, or global observers
- deanonymization caused by account login or user behavior
- targeted exploitation
- all browser fingerprinting vectors

## Design constraints

1. Privacy and anonymity are separate claims.
2. Telemetry removal alone does not make a browser anonymous.
3. Custom hardening can increase fingerprint uniqueness if it diverges too far from a known cohort.
4. Security-relevant network services need replacement plans before removal.

## Product boundary language

Veil may accurately claim:

- privacy-first browser
- hardened browser
- reduced unsolicited network activity
- reduced product telemetry

Veil must not currently claim:

- anonymous browser
- Tor-equivalent browser
- strong anti-fingerprinting browser in the Tor Browser sense

## Definition of done checkpoints

### Zero telemetry

- compile-time and runtime telemetry-related controls are documented
- telemetry collection and upload distinctions are explicit
- clean-profile verification exists
- the claim document names excluded areas and remaining caveats

### Minimal unsolicited network activity

- pre-navigation network baseline captured
- each outbound request source explained
- dangerous-to-disable features are not silently broken
- the default behavior is justified in writing

### Privacy-first release candidate

- privacy defaults documented
- compatibility regressions reviewed
- fingerprinting impact noted for each nontrivial change
- CI or local automation fails on privacy assertion regressions
