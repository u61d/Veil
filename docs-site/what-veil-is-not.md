# What Veil is not

Veil is not trying to be everything.

## Not claimed

- It is not an anonymity browser.
- It is not a Tor replacement.
- It is not a browser with zero background traffic.
- It is not a browser with every Mozilla-operated service removed.
- It is not a clean compile-time removal of every `MOZ_DATA_REPORTING` surface.
- It is not claiming full browser parity beyond the paths that were actually smoke-tested.

## Why the wording stays narrow

The limits are explicit because the project is trying to keep claims tied to evidence.

Current examples:

- `MOZ_DATA_REPORTING` still resolves true because upstream ties it to a crashreporter-linked aggregate.
- Remote Settings and content-signature traffic are still present by design.
- Crashreporter is still present.
- Some build and verification paths are still Linux- and workspace-specific.

Those limits do not erase the work Veil already does. They do set the boundary for what it can say honestly today.
