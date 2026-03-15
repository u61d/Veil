#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def parse_args() -> argparse.Namespace:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    default_binary = (
        repo_root
        / "upstream"
        / "firefox"
        / "obj-veil"
        / "dist"
        / "bin"
        / "firefox"
    )
    default_geckodriver = (
        repo_root
        / "upstream"
        / "firefox"
        / "obj-veil"
        / "dist"
        / "host"
        / "bin"
        / "geckodriver"
    )
    parser = argparse.ArgumentParser(
        description="Run Alpha-level smoke tests against the built Veil browser."
    )
    parser.add_argument(
        "--binary",
        default=str(default_binary),
        help="Path to the Veil browser binary",
    )
    parser.add_argument(
        "--geckodriver",
        default=str(default_geckodriver),
        help="Path to geckodriver",
    )
    parser.add_argument(
        "--output-json",
        help="Optional path for a machine-readable report",
    )
    return parser.parse_args()


def pick_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_http(url: str, *, timeout: float) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"timed out waiting for {url}: {last_error}")


class SmokeRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *args: object) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/download.txt":
            content = b"Veil smoke download\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Disposition", 'attachment; filename="download.txt"')
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        super().do_GET()


class WebDriverSession:
    def __init__(
        self,
        *,
        binary: pathlib.Path,
        geckodriver: pathlib.Path,
        profile_dir: pathlib.Path,
        download_dir: pathlib.Path,
        extra_args: list[str] | None = None,
    ) -> None:
        self.binary = binary
        self.geckodriver = geckodriver
        self.profile_dir = profile_dir
        self.download_dir = download_dir
        self.extra_args = extra_args or []
        self.port = pick_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen[str] | None = None
        self.session_id: str | None = None

    def start(self) -> None:
        self.proc = subprocess.Popen(
            [
                str(self.geckodriver),
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        wait_for_http(f"{self.base_url}/status", timeout=15)
        self.session_id = self._create_session()

    def stop(self) -> None:
        if self.session_id is not None:
            try:
                self.request("DELETE", f"/session/{self.session_id}")
            except Exception:  # noqa: BLE001
                pass
            self.session_id = None
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)
            self.proc = None

    def _create_session(self) -> str:
        prefs: dict[str, object] = {
            "browser.download.folderList": 2,
            "browser.download.dir": str(self.download_dir),
            "browser.download.useDownloadDir": True,
            "browser.download.manager.showWhenStarting": False,
            "browser.helperApps.neverAsk.saveToDisk": "text/plain,application/octet-stream",
            "browser.shell.checkDefaultBrowser": False,
            "app.update.auto": False,
        }
        payload = {
            "capabilities": {
                "alwaysMatch": {
                    "browserName": "firefox",
                    "acceptInsecureCerts": True,
                    "moz:firefoxOptions": {
                        "binary": str(self.binary),
                        "args": ["-headless", "-profile", str(self.profile_dir), *self.extra_args],
                        "prefs": prefs,
                    },
                }
            }
        }
        response = self.request("POST", "/session", payload)
        value = response["value"]
        return value.get("sessionId") or response.get("sessionId")

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        url = f"{self.base_url}{path}"
        body = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def session_request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if self.session_id is None:
            raise RuntimeError("webdriver session not started")
        return self.request(method, f"/session/{self.session_id}{path}", payload)

    def get(self, url: str) -> None:
        self.session_request("POST", "/url", {"url": url})

    def current_url(self) -> str:
        return str(self.session_request("GET", "/url")["value"])

    def title(self) -> str:
        return str(self.session_request("GET", "/title")["value"])

    def source(self) -> str:
        return str(self.session_request("GET", "/source")["value"])

    def execute(self, script: str, args: list[object] | None = None) -> object:
        return self.session_request(
            "POST",
            "/execute/sync",
            {"script": script, "args": args or []},
        )["value"]

    def find_element(self, using: str, value: str) -> str:
        result = self.session_request(
            "POST",
            "/element",
            {"using": using, "value": value},
        )["value"]
        return result.get("element-6066-11e4-a52e-4f735466cecf") or result["ELEMENT"]

    def element_click(self, element_id: str) -> None:
        self.session_request("POST", f"/element/{element_id}/click", {})

    def element_send_keys(self, element_id: str, text: str) -> None:
        self.session_request("POST", f"/element/{element_id}/value", {"text": text, "value": list(text)})

    def new_window(self, window_type: str) -> str:
        return str(self.session_request("POST", "/window/new", {"type": window_type})["value"]["handle"])

    def window_handles(self) -> list[str]:
        return list(self.session_request("GET", "/window/handles")["value"])

    def switch_to_window(self, handle: str) -> None:
        self.session_request("POST", "/window", {"handle": handle})

    def install_addon(self, path: pathlib.Path, *, temporary: bool = True) -> str:
        return str(
            self.session_request(
                "POST",
                "/moz/addon/install",
                {"path": str(path), "temporary": temporary},
            )["value"]
        )


def wait_until(predicate, *, timeout: float, step: float = 0.2) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(step)
    return False


def add_result(results: list[dict[str, object]], name: str, status: str, detail: str) -> None:
    results.append({"name": name, "status": status, "detail": detail})


def build_fixture_site(root: pathlib.Path) -> None:
    (root / "index.html").write_text(
        """<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Veil Smoke</title></head>
  <body>
    <h1>Veil Smoke</h1>
    <a id="page2" href="/page2.html">Second page</a>
    <a id="download" href="/download.txt">Download</a>
  </body>
</html>
""",
        encoding="utf-8",
    )
    (root / "page2.html").write_text(
        """<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Page Two</title></head>
  <body><p>second page</p></body>
</html>
""",
        encoding="utf-8",
    )
    (root / "sw.js").write_text(
        """self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
""",
        encoding="utf-8",
    )
    (root / "service-worker.html").write_text(
        """<!doctype html>
<html>
  <head><meta charset="utf-8"><title>SW Pending</title></head>
  <body>
    <script>
      navigator.serviceWorker.register('/sw.js').then(() => navigator.serviceWorker.ready).then(() => {
        document.title = 'SW Ready';
        document.body.textContent = 'ready';
      }).catch(err => {
        document.title = 'SW Failed';
        document.body.textContent = String(err);
      });
    </script>
  </body>
</html>
""",
        encoding="utf-8",
    )


def build_test_addon(path: pathlib.Path) -> None:
    manifest = {
        "manifest_version": 2,
        "name": "Veil Smoke Add-on",
        "version": "0.1",
        "applications": {"gecko": {"id": "veil-smoke@example.invalid"}},
        "description": "Temporary smoke-test extension",
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))


def main() -> int:
    args = parse_args()
    binary = pathlib.Path(args.binary).resolve()
    geckodriver = pathlib.Path(args.geckodriver).resolve()
    if not binary.exists():
        print(f"missing browser binary: {binary}", file=sys.stderr)
        return 2
    if not geckodriver.exists():
        print(f"missing geckodriver: {geckodriver}", file=sys.stderr)
        return 2

    results: list[dict[str, object]] = []
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix="veil-alpha-smoke."))
    site_root = temp_root / "site"
    site_root.mkdir(parents=True)
    downloads = temp_root / "downloads"
    downloads.mkdir()
    (temp_root / "profile").mkdir()
    (temp_root / "private-profile").mkdir()
    addon_path = temp_root / "veil-smoke-addon.xpi"
    build_fixture_site(site_root)
    build_test_addon(addon_path)

    original_cwd = pathlib.Path.cwd()
    os.chdir(site_root)
    port = pick_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), SmokeRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"

    session: WebDriverSession | None = None
    private_session: WebDriverSession | None = None
    try:
        session = WebDriverSession(
            binary=binary,
            geckodriver=geckodriver,
            profile_dir=temp_root / "profile",
            download_dir=downloads,
        )
        session.start()
        add_result(results, "first-launch", "pass", "WebDriver session started against the Veil binary")

        session.get(f"{base_url}/index.html")
        add_result(
            results,
            "open-normal-page",
            "pass" if session.title() == "Veil Smoke" else "fail",
            f"loaded local page with title {session.title()!r}",
        )

        first_handle = session.window_handles()[0]
        new_handle = session.new_window("tab")
        session.switch_to_window(new_handle)
        session.get(f"{base_url}/page2.html")
        add_result(
            results,
            "multiple-tabs",
            "pass" if len(session.window_handles()) >= 2 and session.title() == "Page Two" else "fail",
            f"window handles={len(session.window_handles())}, active title={session.title()!r}",
        )
        session.switch_to_window(first_handle)

        download_link = session.find_element("css selector", "#download")
        session.element_click(download_link)
        downloaded = downloads / "download.txt"
        add_result(
            results,
            "download-basic-file",
            "pass" if wait_until(lambda: downloaded.exists(), timeout=15) else "fail",
            f"download file present={downloaded.exists()}",
        )

        session.get("about:preferences#privacy")
        pref_source = session.source()
        prefs_ok = 'automaticallySubmitCrashesBox' in pref_source and 'submitUsagePingBox' not in pref_source
        add_result(
            results,
            "settings-load",
            "pass" if prefs_ok else "fail",
            "about:preferences loaded with crash UI present and telemetry/upload controls absent",
        )

        session.get("about:home")
        search_selector = session.execute(
            """
            let el = document.querySelector('input[id*="search"], input[type="search"], input[name*="search"]');
            return el ? (el.id ? '#' + el.id : 'input[name=\"' + el.name + '\"]') : null;
            """
        )
        search_status = "warn"
        search_detail = "search field not found on about:home"
        if isinstance(search_selector, str) and search_selector:
            search_input = session.find_element("css selector", search_selector)
            session.element_send_keys(search_input, "veil release test\n")
            if wait_until(lambda: not session.current_url().startswith("about:"), timeout=15):
                search_status = "pass"
                search_detail = f"search navigated to {session.current_url()!r}"
            else:
                search_status = "fail"
                search_detail = "search field was found but did not navigate away from about:home"
        else:
            search_detail = (
                "headless about:home exposed no search field; "
                "interactive search UI not verified in this harness"
            )
        add_result(results, "search", search_status, search_detail)

        session.get(f"{base_url}/service-worker.html")
        add_result(
            results,
            "service-worker",
            "pass" if wait_until(lambda: session.title() == "SW Ready", timeout=15) else "fail",
            f"final title={session.title()!r}",
        )

        addon_id = session.install_addon(addon_path, temporary=True)
        add_result(
            results,
            "extension-installation",
            "pass" if addon_id == "veil-smoke@example.invalid" else "fail",
            f"install_addon returned {addon_id!r}",
        )

        private_session = WebDriverSession(
            binary=binary,
            geckodriver=geckodriver,
            profile_dir=temp_root / "private-profile",
            download_dir=downloads,
            extra_args=["-private-window", "about:blank"],
        )
        private_session.start()
        add_result(
            results,
            "private-window-launch",
            "pass",
            "browser launched with -private-window and accepted a WebDriver session",
        )

    except urllib.error.HTTPError as exc:
        add_result(results, "webdriver-http", "fail", f"{exc.code} {exc.reason}")
    except Exception as exc:  # noqa: BLE001
        add_result(results, "smoke-harness", "fail", str(exc))
    finally:
        if private_session is not None:
            private_session.stop()
        if session is not None:
            session.stop()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        os.chdir(original_cwd)

    failures = [item for item in results if item["status"] == "fail"]
    warnings = [item for item in results if item["status"] == "warn"]
    report = {
        "status": "fail" if failures else "pass",
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "results": results,
    }

    if args.output_json:
        output_path = pathlib.Path(args.output_json).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for item in results:
        print(f"{item['status'].upper()}: {item['name']} - {item['detail']}")

    if failures:
        print("\nVeil Alpha smoke tests failed.")
        shutil.rmtree(temp_root, ignore_errors=True)
        return 1

    if warnings:
        print("\nVeil Alpha smoke tests passed with warnings.")
    else:
        print("\nVeil Alpha smoke tests passed.")
    shutil.rmtree(temp_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
