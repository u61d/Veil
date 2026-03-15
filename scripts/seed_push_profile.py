#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed a Firefox profile with persisted Push state for Veil verification."
    )
    parser.add_argument("objdir", help="Firefox objdir, for example upstream/firefox/obj-veil")
    parser.add_argument("profile_dir", help="Profile directory to seed")
    parser.add_argument(
        "--mode",
        choices=("subscription", "broadcast", "both"),
        default="subscription",
        help="Persisted Push state to create, default: subscription",
    )
    parser.add_argument(
        "--user-agent-id",
        help="Optional dom.push.userAgentID value to preseed",
    )
    args = parser.parse_args()

    objdir = pathlib.Path(args.objdir).resolve()
    dist_bin = objdir / "dist/bin"
    xpcshell = dist_bin / "xpcshell"
    chrome_manifest = dist_bin / "chrome.manifest"
    seed_js = pathlib.Path(__file__).with_name("seed_push_profile.js")

    for required in (xpcshell, chrome_manifest, seed_js):
        if not required.exists():
            print(f"missing required file: {required}", file=sys.stderr)
            return 2

    profile_dir = pathlib.Path(args.profile_dir).resolve()
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    existing_library_path = env.get("LD_LIBRARY_PATH")
    env["LD_LIBRARY_PATH"] = (
        str(dist_bin)
        if not existing_library_path
        else f"{dist_bin}:{existing_library_path}"
    )
    env["XPCSHELL_TEST_PROFILE_DIR"] = str(profile_dir)
    env["VEIL_PUSH_PROFILE_MODE"] = args.mode
    if args.user_agent_id:
        env["VEIL_PUSH_USER_AGENT_ID"] = args.user_agent_id

    cmd = [
        str(xpcshell),
        "-g",
        str(dist_bin),
        "-a",
        str(dist_bin),
        "-r",
        str(chrome_manifest),
        "-f",
        str(seed_js),
    ]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=dist_bin,
        timeout=30,
    )
    json_line = next(
        (
            line
            for line in completed.stdout.splitlines()
            if line.strip().startswith("{") and line.strip().endswith("}")
        ),
        None,
    )
    if json_line is None:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        print("seed profile did not emit structured output", file=sys.stderr)
        return completed.returncode or 1

    result = json.loads(json_line)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
