# What Veil is

Veil is a patch-managed Firefox fork.

The project is trying to do a small number of things well:

- disable product telemetry by default
- reduce unsolicited startup traffic
- keep the fork close enough to upstream that rebases stay realistic
- document claims and limits instead of hand-waving them

## Current safe description

The current release-safe description is:

> Veil Alpha is a Firefox-based fork that disables product telemetry by default, suppresses the main telemetry and data-reporting startup state seen in stock Firefox, and reduces clean-profile startup traffic while keeping the Mozilla update and configuration services it still depends on.

## What that means in practice

- Veil changes both compile-time and runtime behavior.
- The main claims are checked against packaged runtime artifacts, not just source edits.
- The project still keeps Mozilla-operated Remote Settings and content-signature traffic because those are part of the current security-sensitive update/configuration path.

## Maintenance model

Veil is not maintained as a long-lived separate browser tree. The repo carries a patch queue, verification scripts, and maintenance notes.

If you are working on the fork itself, the deeper engineering notes remain in the repo:

- [patch inventory](https://github.com/u61d/Veil/blob/main/patches/patch-inventory.json)
- [rebase strategy](https://github.com/u61d/Veil/blob/main/docs/rebase-strategy.md)
- [release claims](https://github.com/u61d/Veil/blob/main/docs/release-claims.md)
