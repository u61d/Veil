# Veil Release Claims

Status date: `2026-03-15`

## Safe Alpha claim language

Use language like:

- "Veil is a privacy-first Firefox-based fork with telemetry disabled by default."
- "Veil reduces clean-profile startup network activity and keeps a small set of security-sensitive Mozilla service connections by default."
- "Veil does not market itself as an anonymity browser or Tor replacement."
- "Veil's current claims are backed by patch replay checks, packaged-runtime verification, startup network measurement, and Alpha smoke tests."

## Claims that must stay qualified

- "Zero telemetry"
  - Not yet safe without qualification because `MOZ_DATA_REPORTING` still remains enabled at build time.
- "Minimal unsolicited network activity"
  - Must stay qualified because Remote Settings and content-signature traffic remain intentionally enabled.
- "Preserves core browser functionality"
  - Keep this narrow. Current evidence supports basic browsing, downloads, settings, temporary extensions, service workers, private-window launch, and Push regression coverage. It does not prove every browser path.
- "Anti-fingerprinting"
  - Must stay conservative until a separate, measured hardening phase is complete.
- "Reproducible build"
  - Not yet safe as release-facing wording while fresh configure still depends on local toolchain state in this workspace.

## Claims to avoid

- "Anonymous browser"
- "Tor alternative"
- "No network traffic"
- "All Mozilla services removed"
- "Crash reporting removed"

## Short Alpha description

Suggested short description:

> Veil Alpha is a Firefox-based fork that disables product telemetry by default, suppresses the main telemetry and data-reporting startup state seen in stock Firefox, and reduces clean-profile startup traffic while keeping the Mozilla update and configuration services it still depends on.
