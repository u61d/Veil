#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Iterable


EXPECTED_FIREFOX_PREFS = {
    "browser.newtabpage.activity-stream.telemetry.privatePing.enabled": "false",
    "browser.newtabpage.activity-stream.telemetry.privatePing.redactNewtabPing.enabled": "false",
    "datareporting.healthreport.uploadEnabled": "false",
    "datareporting.usage.uploadEnabled": "false",
    "datareporting.policy.dataSubmissionEnabled": "false",
    "datareporting.policy.dataSubmissionPolicyBypassNotification": "true",
    "datareporting.policy.firstRunURL": '""',
    "toolkit.telemetry.reportingpolicy.firstRun": "false",
    "browser.region.network.url": '""',
    "network.connectivity-service.enabled": "false",
    "network.captive-portal-service.enabled": "false",
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
}

EXPECTED_MISSING_DEFINES = (
    "MOZ_TELEMETRY_REPORTING",
    "MOZ_SERVICES_HEALTHREPORT",
    "MOZ_NORMANDY",
)

GREPREFS_ABSENCE_MARKERS = (
    'pref("datareporting.healthreport.infoURL"',
    'pref("datareporting.healthreport.uploadEnabled"',
    'pref("datareporting.usage.uploadEnabled"',
    'pref("datareporting.policy.dataSubmissionEnabled"',
    'pref("datareporting.policy.firstRunURL"',
)

PRIVACY_UI_ABSENCE_MARKERS = (
    'id="telemetry-container"',
    'id="optOutStudiesEnabled"',
    'id="enableNimbusRollouts"',
    'id="submitHealthReportBox"',
    'id="submitUsagePingBox"',
    'id="addonRecommendationEnabled"',
)

PRIVACY_UI_PRESENCE_MARKERS = (
    'id="automaticallySubmitCrashesBox"',
)

BROWSER_COMPONENTS_ABSENCE_MARKERS = (
    "resource://normandy/Normandy.sys.mjs Normandy.init",
    "resource://normandy/Normandy.sys.mjs Normandy.uninit",
)


def pref_regex(pref_name: str, expected_value: str) -> re.Pattern[str]:
    if expected_value in {"true", "false"}:
        return re.compile(
            rf'pref\("{re.escape(pref_name)}",\s*{expected_value}\s*\);'
        )
    return re.compile(
        rf'pref\("{re.escape(pref_name)}",\s*{re.escape(expected_value)}\s*\);'
    )


def find_first(base: pathlib.Path, patterns: Iterable[str]) -> pathlib.Path | None:
    for pattern in patterns:
        matches = sorted(base.glob(pattern))
        if matches:
            return matches[0]
    return None


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


def run_xpcshell_probe(
    checks: list[dict[str, object]],
    *,
    objdir: pathlib.Path,
) -> None:
    dist_bin = objdir / "dist/bin"
    xpcshell = dist_bin / "xpcshell"
    chrome_manifest = dist_bin / "chrome.manifest"
    if not xpcshell.exists() or not chrome_manifest.exists():
        add_check(
            checks,
            name="xpcshell-appconstants",
            result="warn",
            detail="xpcshell or chrome.manifest missing; AppConstants runtime probe skipped",
        )
        return

    env = os.environ.copy()
    existing_library_path = env.get("LD_LIBRARY_PATH")
    env["LD_LIBRARY_PATH"] = (
        str(dist_bin)
        if not existing_library_path
        else f"{dist_bin}:{existing_library_path}"
    )
    cmd = [
        str(xpcshell),
        "-g",
        str(dist_bin),
        "-a",
        str(dist_bin),
        "-r",
        str(chrome_manifest),
        "-e",
        (
            'const { AppConstants } = ChromeUtils.importESModule('
            '"resource://gre/modules/AppConstants.sys.mjs"); '
            "print(JSON.stringify({telemetry: AppConstants.MOZ_TELEMETRY_REPORTING, "
            "dataReporting: AppConstants.MOZ_DATA_REPORTING, "
            "normandy: AppConstants.MOZ_NORMANDY}));"
        ),
    ]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=dist_bin,
    )
    json_line = next(
        (
            line
            for line in completed.stdout.splitlines()
            if line.strip().startswith("{") and line.strip().endswith("}")
        ),
        None,
    )
    if completed.returncode != 0 or json_line is None:
        add_check(
            checks,
            name="xpcshell-appconstants",
            result="warn",
            detail="xpcshell AppConstants probe did not return structured output",
            path=xpcshell,
        )
        return

    values = json.loads(json_line)
    add_check(
        checks,
        name="xpcshell:AppConstants.MOZ_TELEMETRY_REPORTING",
        result="pass" if values["telemetry"] is False else "fail",
        detail=f"expected false, saw {values['telemetry']!r}",
        path=xpcshell,
    )
    add_check(
        checks,
        name="xpcshell:AppConstants.MOZ_NORMANDY",
        result="pass" if values["normandy"] is False else "fail",
        detail=f"expected false, saw {values['normandy']!r}",
        path=xpcshell,
    )
    add_check(
        checks,
        name="xpcshell:AppConstants.MOZ_DATA_REPORTING",
        result="warn" if values["dataReporting"] is True else "pass",
        detail=(
            "expected caveated true while crashreporter remains enabled, "
            f"saw {values['dataReporting']!r}"
        ),
        path=xpcshell,
    )


def verify_file_pref_defaults(
    checks: list[dict[str, object]],
    path: pathlib.Path,
) -> None:
    text = path.read_text(encoding="utf-8")
    for pref_name, expected_value in EXPECTED_FIREFOX_PREFS.items():
        matched = bool(pref_regex(pref_name, expected_value).search(text))
        add_check(
            checks,
            name=f"firefox-js:{pref_name}",
            result="pass" if matched else "fail",
            detail=f"expected {pref_name}={expected_value}",
            path=path,
        )


def verify_marker_absence(
    checks: list[dict[str, object]],
    *,
    label: str,
    path: pathlib.Path,
    markers: Iterable[str],
) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        missing = marker not in text
        add_check(
            checks,
            name=f"{label}:absent:{marker}",
            result="pass" if missing else "fail",
            detail=f"expected marker to be absent: {marker}",
            path=path,
        )


def verify_marker_presence(
    checks: list[dict[str, object]],
    *,
    label: str,
    path: pathlib.Path,
    markers: Iterable[str],
) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        present = marker in text
        add_check(
            checks,
            name=f"{label}:present:{marker}",
            result="pass" if present else "warn",
            detail=f"expected marker to be present: {marker}",
            path=path,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify Veil telemetry-related build assertions against the current "
            "objdir and any built browser artifacts that are available."
        )
    )
    parser.add_argument("objdir", help="Firefox objdir, for example upstream/firefox/obj-veil")
    parser.add_argument(
        "--output-json",
        help="Optional path for a machine-readable verification report",
    )
    args = parser.parse_args()

    objdir = pathlib.Path(args.objdir).resolve()
    checks: list[dict[str, object]] = []

    mozconfig_json = objdir / ".mozconfig.json"
    if not mozconfig_json.exists():
        print(f"missing required file: {mozconfig_json}", file=sys.stderr)
        return 2

    config_status_json = objdir / "config.status.json"
    if not config_status_json.exists():
        print(f"missing required file: {config_status_json}", file=sys.stderr)
        return 2

    mozconfig = json.loads(mozconfig_json.read_text(encoding="utf-8"))
    configure_args = mozconfig["mozconfig"]["configure_args"]
    telemetry_arg_present = "MOZ_TELEMETRY_REPORTING=" in configure_args
    add_check(
        checks,
        name="configure-arg:MOZ_TELEMETRY_REPORTING",
        result="pass" if telemetry_arg_present else "fail",
        detail="Veil mozconfig should explicitly unset MOZ_TELEMETRY_REPORTING",
        path=mozconfig_json,
    )

    config_status = json.loads(config_status_json.read_text(encoding="utf-8"))
    defines = config_status.get("defines", {})
    for define_name in EXPECTED_MISSING_DEFINES:
        add_check(
            checks,
            name=f"compile-time-define:{define_name}",
            result="pass" if define_name not in defines else "fail",
            detail=f"{define_name} should not be defined in the Veil build configuration",
            path=config_status_json,
        )

    data_reporting_defined = "MOZ_DATA_REPORTING" in defines
    add_check(
        checks,
        name="compile-time-define:MOZ_DATA_REPORTING",
        result="warn" if data_reporting_defined else "pass",
        detail=(
            "MOZ_DATA_REPORTING remains enabled when crashreporter still contributes "
            "to the aggregate gate; this is a documented boundary, not an automatic failure"
        ),
        path=config_status_json,
    )

    firefox_js = find_first(
        objdir,
        (
            "dist/bin/browser/defaults/preferences/firefox.js",
            "dist/bin/**/preferences/firefox.js",
            "dist/bin/**/pref/firefox.js",
            "dist/bin/**/firefox.js",
        ),
    )
    if firefox_js is None:
        add_check(
            checks,
            name="built-defaults:firefox.js",
            result="warn",
            detail="built firefox.js not found yet; final packaging or install stage may still be pending",
        )
    else:
        verify_file_pref_defaults(checks, firefox_js)

    greprefs = objdir / "dist/bin/greprefs.js"
    if not greprefs.exists():
        add_check(
            checks,
            name="built-defaults:greprefs.js",
            result="warn",
            detail="built greprefs.js not found yet; compile-time pref verification is incomplete",
        )
    else:
        verify_marker_absence(
            checks,
            label="greprefs",
            path=greprefs,
            markers=GREPREFS_ABSENCE_MARKERS,
        )
    privacy_ui = find_first(
        objdir,
        (
            "dist/bin/browser/chrome/browser/content/browser/preferences/preferences.xhtml",
            "**/preferences.xhtml",
            "**/privacy.inc.xhtml",
            "dist/bin/browser/**/privacy.inc.xhtml",
        ),
    )
    if privacy_ui is None:
        add_check(
            checks,
            name="privacy-ui",
            result="warn",
            detail="built preferences UI not found yet; UI surface verification is incomplete",
        )
    else:
        verify_marker_absence(
            checks,
            label="privacy-ui",
            path=privacy_ui,
            markers=PRIVACY_UI_ABSENCE_MARKERS,
        )
        verify_marker_presence(
            checks,
            label="privacy-ui",
            path=privacy_ui,
            markers=PRIVACY_UI_PRESENCE_MARKERS,
        )

    browser_components_manifest = find_first(
        objdir,
        (
            "dist/bin/browser/**/BrowserComponents.manifest",
            "**/BrowserComponents.manifest",
        ),
    )
    if browser_components_manifest is None:
        add_check(
            checks,
            name="browser-components-manifest",
            result="warn",
            detail=(
                "preprocessed BrowserComponents.manifest not found yet; Normandy "
                "startup registration verification is incomplete"
            ),
        )
    else:
        verify_marker_absence(
            checks,
            label="browser-components-manifest",
            path=browser_components_manifest,
            markers=BROWSER_COMPONENTS_ABSENCE_MARKERS,
        )

    browser_main = find_first(
        objdir,
        (
            "dist/bin/browser/chrome/browser/content/browser/browser-main.js",
            "**/browser-main.js",
        ),
    )
    if browser_main is not None:
        verify_marker_absence(
            checks,
            label="browser-main",
            path=browser_main,
            markers=("browser-data-submission-info-bar.js",),
        )

    browser_init = find_first(
        objdir,
        (
            "dist/bin/browser/chrome/browser/content/browser/browser-init.js",
            "**/browser-init.js",
        ),
    )
    if browser_init is not None:
        verify_marker_absence(
            checks,
            label="browser-init",
            path=browser_init,
            markers=("gDataNotificationInfoBar.init()",),
        )

    run_xpcshell_probe(checks, objdir=objdir)

    failures = [check for check in checks if check["result"] == "fail"]
    warnings = [check for check in checks if check["result"] == "warn"]

    report = {
        "objdir": str(objdir),
        "status": "fail" if failures else "pass",
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "checks": checks,
    }

    if args.output_json:
        output_path = pathlib.Path(args.output_json).resolve()
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for check in checks:
        prefix = check["result"].upper()
        print(f"{prefix}: {check['name']} - {check['detail']}")
        if "path" in check:
            print(f"  {check['path']}")

    if failures:
        print("\nVeil build-backed telemetry assertions failed.")
        return 1

    print("\nVeil build-backed telemetry assertions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
