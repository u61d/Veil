#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys


def run_git(args: list[str], cwd: pathlib.Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report Veil patches that touch files changed upstream."
    )
    parser.add_argument("upstream", help="Path to the upstream Firefox checkout")
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base revision for git diff (default: origin/main)",
    )
    parser.add_argument(
        "--target",
        default="HEAD",
        help="Target revision for git diff (default: HEAD)",
    )
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    upstream = pathlib.Path(args.upstream).resolve()
    inventory_path = repo_root / "patches" / "patch-inventory.json"

    if not upstream.exists():
        print(f"missing upstream checkout: {upstream}", file=sys.stderr)
        return 2

    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    changed_files = {
        line.strip()
        for line in run_git(
            ["diff", "--name-only", f"{args.base}..{args.target}"], upstream
        ).splitlines()
        if line.strip()
    }

    impacted = []
    for patch in inventory["patches"]:
        touched = set(patch.get("upstream_files", []))
        overlap = sorted(touched & changed_files)
        if overlap:
            impacted.append((patch["id"], patch["title"], overlap))

    if not impacted:
        print("No Veil patches overlap files changed in the selected upstream diff.")
        return 0

    for patch_id, title, overlap in impacted:
        print(f"{patch_id}: {title}")
        for path in overlap:
            print(f"  {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
