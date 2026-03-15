#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import pathlib
import sys


EXPECTED_MARKERS = (
    '"datareporting.dau.cachedUsageProfileID"',
    '"datareporting.dau.cachedUsageProfileGroupID"',
    '"datareporting.healthreport.uploadEnabled"',
    '"datareporting.usage.uploadEnabled"',
    "datareporting.policy.",
)


def add_check(
    checks: list[dict[str, object]],
    *,
    name: str,
    result: str,
    detail: str,
    path: pathlib.Path | None = None,
) -> None:
    record: dict[str, object] = {
        "name": name,
        "result": result,
        "detail": detail,
    }
    if path is not None:
        record["path"] = str(path)
    checks.append(record)


def verify_file(
    checks: list[dict[str, object]],
    *,
    label: str,
    path: pathlib.Path,
) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in EXPECTED_MARKERS:
        add_check(
            checks,
            name=f"{label}:{marker}",
            result="pass" if marker in text else "fail",
            detail=f"expected ignore-list coverage marker in {label}: {marker}",
            path=path,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that Veil's backup resource still contains the ignore-list "
            "coverage for data-reporting prefs and policy state in both source "
            "and built artifacts."
        )
    )
    parser.add_argument(
        "--srcdir",
        default="upstream/firefox",
        help="Firefox source tree, defaults to upstream/firefox",
    )
    parser.add_argument(
        "--objdir",
        default="upstream/firefox/obj-veil",
        help="Firefox objdir, defaults to upstream/firefox/obj-veil",
    )
    parser.add_argument(
        "--output-json",
        help="Optional path for a machine-readable verification report",
    )
    args = parser.parse_args()

    srcdir = pathlib.Path(args.srcdir).resolve()
    objdir = pathlib.Path(args.objdir).resolve()

    source_file = (
        srcdir
        / "browser/components/backup/resources/PreferencesBackupResource.sys.mjs"
    )
    built_file = (
        objdir / "dist/bin/browser/modules/backup/PreferencesBackupResource.sys.mjs"
    )

    checks: list[dict[str, object]] = []

    for label, path in (("source", source_file), ("built", built_file)):
        if not path.exists():
            add_check(
                checks,
                name=f"{label}:exists",
                result="fail",
                detail=f"required file missing: {path}",
                path=path,
            )
            continue
        verify_file(checks, label=label, path=path)

    failures = [check for check in checks if check["result"] == "fail"]
    report = {
        "status": "fail" if failures else "pass",
        "failure_count": len(failures),
        "checks": checks,
    }

    if args.output_json:
        output_path = pathlib.Path(args.output_json).resolve()
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for check in checks:
        print(f"{check['result'].upper()}: {check['name']} - {check['detail']}")
        if "path" in check:
            print(f"  {check['path']}")

    if failures:
        print("\nVeil backup data-reporting surface verification failed.")
        return 1

    print("\nVeil backup data-reporting surface verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
