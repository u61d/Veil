# Ranked Implementation Plan

Ranking is based on privacy impact first, maintenance cost second.

| Rank | Work item | Expected impact | Maintenance cost | Notes |
| --- | --- | --- | --- | --- |
| 1 | Land telemetry and study default-off patch set | Very high | Low | Core promise, minimal invasive change, already started. |
| 2 | Add source assertions and patch application tooling | High | Low | Prevents privacy regressions and supports rebases. |
| 3 | Build compile-time disable layer for telemetry, health report, and Normandy | High | Medium | Reduces code surface beyond pref-only suppression. |
| 4 | Capture clean-profile network baseline before and after patches | High | Medium | Converts assumptions into measured evidence. |
| 5 | Disable low-risk vendor-linked services by default | High | Medium | Discovery, Contile, New Tab fetches, search suggestions, speculative network paths. |
| 6 | Rebrand product metadata and unofficial branding surfaces for Veil redistribution | Medium | Medium | Required before distribution; legal and packaging relevance. |
| 7 | Add conservative privacy defaults with compatibility notes | High | Medium | Must avoid fingerprint-unique settings dumps. |
| 8 | Keep updates and security-linked services safe while reducing vendor coupling | High | High | Needs replacement design, not just deletion. |
| 9 | Implement safe anti-fingerprinting subset informed by Tor Browser research | Medium | High | Only after baseline build, audit, and measurements exist. |
| 10 | Add CI and runtime clean-profile verification | High | High | Needed for credible release readiness. |

## Immediate next sequence

1. Prove the authored patches apply to current upstream files.
2. Expand source assertions to cover the first network-suppression patch.
3. Import or bootstrap an upstream checkout and start compile-time telemetry-disable work.
4. Build the first local Veil artifact and capture pre-navigation network traffic.
