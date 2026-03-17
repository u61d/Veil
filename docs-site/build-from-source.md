# Build from source

The current known-good build path is Linux x86_64.

Veil is still a patch-managed fork. Building it means:

1. acquiring the pinned upstream source snapshot
2. applying the Veil patch queue
3. using the Veil build wrapper for the current Linux toolchain path

## Current workflow

From the repo root:

```bash
./scripts/bootstrap_upstream_firefox.sh
./scripts/apply_veil_patches.sh
./scripts/rebuild_veil_linux_clean.sh
```

## What to expect

- The rebuild wrapper handles the current Arch/WASI toolchain workaround used in this workspace.
- The produced Linux runtime is the same one Veil currently packages for Alpha.
- Fresh configure is still sensitive to local toolchain state if you bypass the wrapper and try to assemble the environment by hand.

## Deeper notes

The detailed build note stays in the repo:

- [build notes](https://github.com/u61d/Veil/blob/main/docs/build-notes.md)

The current patch queue description also stays in the repo:

- [patch inventory](https://github.com/u61d/Veil/blob/main/patches/patch-inventory.json)
