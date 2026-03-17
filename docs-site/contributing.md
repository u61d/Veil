# Contributing

Veil is a patch-managed fork. Keep changes small, explain them clearly, and keep claims tied to evidence.

## Before you touch release-facing wording

Read:

- [release claims](https://github.com/u61d/Veil/blob/main/docs/release-claims.md)
- [known limitations](https://github.com/u61d/Veil/blob/main/docs/known-limitations.md)
- [rebase strategy](https://github.com/u61d/Veil/blob/main/docs/rebase-strategy.md)
- [patch inventory](https://github.com/u61d/Veil/blob/main/patches/patch-inventory.json)

If your change affects telemetry, startup traffic, or product claims, update the matching docs and rerun the relevant verifiers.

## Preview the docs site locally

```bash
python3 -m venv .venv-docs
. .venv-docs/bin/activate
pip install -r requirements-docs.txt
mkdocs serve
```

The site source lives under `docs-site/`.

The docs toolchain is pinned in `requirements-docs.txt`. Do not swap it to `latest` casually. The current pin is based on `mkdocs-material==9.7.5`, which is the Material release that explicitly limits MkDocs to `<2` again.

For a CI-style build:

```bash
mkdocs build --strict
```

## How Pages deploys

The repo uses a GitHub Actions workflow at `.github/workflows/docs.yml`.

On pushes to `main` that touch the docs-site files or the docs workflow:

1. the workflow installs the pinned docs toolchain from `requirements-docs.txt`
2. it runs `mkdocs build --strict`
3. it uploads the built site to GitHub Pages

Pull requests build the docs but do not deploy them.

If Pages is not configured yet, set:

- **Settings → Pages → Build and deployment → Source** = `GitHub Actions`

## Keep the wording sober

- Do not overstate Veil's privacy claims.
- Do not market Veil as anonymous.
- Do not write around known limits.
- Do not add placeholder pages for features Veil does not ship.
