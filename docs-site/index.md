# Veil docs

Veil is a Firefox-based fork with a narrow goal: reduce product telemetry and background traffic without pretending to be something it is not.

This site is the public project manual. It covers the current Alpha claim boundary, install path, build path, and verification workflow.

## Current verified boundary

- Product telemetry is disabled by default.
- The main telemetry and data-reporting startup state seen in stock Firefox is suppressed.
- Clean-profile startup traffic is reduced.
- Mozilla update and configuration services that Veil still depends on remain in place.

## What this site does not claim

- Veil is not presented as an anonymity browser.
- Veil is not presented as a Tor replacement.
- Veil does not claim zero network traffic.
- Veil does not claim every `MOZ_DATA_REPORTING` path is gone at build time.

## Current release

The current public release is **Veil Alpha 1**.

- GitHub prerelease: [u61d/Veil releases](https://github.com/u61d/Veil/releases)
- Current packaged artifact: `veil-alpha1-linux-x86_64.tar.gz`
- Current public platform: Linux x86_64

## Read next

- Start with [Install](install.md) if you want to run the current Alpha release.
- Read [Verification](verification.md) for the checks behind the current claim boundary.
- Read [Known limitations](known-limitations.md) before treating Veil as more than an Alpha.
