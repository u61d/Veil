#!/usr/bin/env python3

from __future__ import annotations

import pathlib
import re
import sys


EXPECTED_PREFS = {
    "browser/app/profile/firefox.js": {
        "browser.newtabpage.activity-stream.telemetry.privatePing.enabled": "false",
        "browser.newtabpage.activity-stream.telemetry.privatePing.redactNewtabPing.enabled": "false",
        "toolkit.telemetry.archive.enabled": "false",
        "toolkit.telemetry.shutdownPingSender.enabled": "false",
        "toolkit.telemetry.firstShutdownPing.enabled": "false",
        "toolkit.telemetry.newProfilePing.enabled": "false",
        "toolkit.telemetry.updatePing.enabled": "false",
        "toolkit.telemetry.bhrPing.enabled": "false",
        "app.shield.optoutstudies.enabled": "false",
        "app.normandy.api_url": '""',
        "browser.discovery.enabled": "false",
        "browser.topsites.contile.enabled": "false",
        "browser.newtab.preload": "false",
    },
    "modules/libpref/init/StaticPrefList.yaml": {
        "datareporting.healthreport.uploadEnabled": "false",
        "privacy.partition.network_state": "true",
    },
}


def pref_regex(pref_name: str, expected_value: str) -> re.Pattern[str]:
    if expected_value in {"true", "false"}:
        return re.compile(
            rf'pref\("{re.escape(pref_name)}",\s*{expected_value}\s*\);'
        )
    return re.compile(
        rf'pref\("{re.escape(pref_name)}",\s*{re.escape(expected_value)}\s*\);'
    )


def static_pref_regex(pref_name: str, expected_value: str) -> re.Pattern[str]:
    return re.compile(
        rf"- name: {re.escape(pref_name)}\n(?:  .*\n)*?  value: {re.escape(expected_value)}\n",
        re.MULTILINE,
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_telemetry_source_assertions.py <upstream-checkout>", file=sys.stderr)
        return 2

    upstream = pathlib.Path(sys.argv[1]).resolve()
    failures: list[str] = []

    for rel_path, prefs in EXPECTED_PREFS.items():
        path = upstream / rel_path
        if not path.exists():
            failures.append(f"missing file: {rel_path}")
            continue

        text = path.read_text(encoding="utf-8")
        for pref_name, expected_value in prefs.items():
            if rel_path.endswith("StaticPrefList.yaml"):
                pattern = static_pref_regex(pref_name, expected_value)
            else:
                pattern = pref_regex(pref_name, expected_value)

            if not pattern.search(text):
                failures.append(
                    f"expected {pref_name}={expected_value} in {rel_path}"
                )

    if failures:
        print("Veil source assertions failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("Veil source assertions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
