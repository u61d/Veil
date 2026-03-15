#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import time


def terminate_process(proc: subprocess.Popen[bytes], *, timeout: float) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=timeout)


def normalize_remote(remote: str) -> str:
    if remote.startswith("[") and "]:" in remote:
        host, port = remote.rsplit("]:", 1)
        return f"{host[1:]}:{port}"
    return remote


def parse_lsof_remotes(socket_log: pathlib.Path) -> list[str]:
    remotes: set[str] = set()
    arrow_pattern = re.compile(r"->(\S+)")
    for line in socket_log.read_text(encoding="utf-8", errors="replace").splitlines():
        match = arrow_pattern.search(line)
        if match:
            remotes.add(normalize_remote(match.group(1)))
    return sorted(remotes)


def parse_packet_destinations(packet_tsv: pathlib.Path) -> list[dict[str, str]]:
    destinations: dict[tuple[str, str, str], dict[str, str]] = {}
    for raw_line in packet_tsv.read_text(encoding="utf-8", errors="replace").splitlines():
        columns = raw_line.split("\t")
        if len(columns) != 7:
            continue
        frame_time, ip_dst, ipv6_dst, dst_port, dns_name, http_host, tls_sni = columns
        remote_ip = ip_dst or ipv6_dst
        if not remote_ip:
            continue
        record = {
            "remote_ip": remote_ip,
            "remote_port": dst_port,
            "dns_name": dns_name,
            "http_host": http_host,
            "tls_sni": tls_sni,
            "first_seen_epoch": frame_time,
        }
        key = (remote_ip, dst_port, dns_name or http_host or tls_sni)
        destinations.setdefault(key, record)
    return sorted(
        destinations.values(),
        key=lambda item: (
            item["remote_ip"],
            item["remote_port"],
            item["dns_name"],
            item["http_host"],
            item["tls_sni"],
        ),
    )


def collect_profile_pref_matches(profile_dir: pathlib.Path) -> list[str]:
    prefs_js = profile_dir / "prefs.js"
    if not prefs_js.exists():
        return []

    pattern = re.compile(
        r"(telemetry|nimbus|datareporting|dom\.push\.userAgentID|doh-rollout|browser\.search\.region|browser\.region\.update)",
        re.IGNORECASE,
    )
    matches: list[str] = []
    for line in prefs_js.read_text(encoding="utf-8", errors="replace").splitlines():
        if pattern.search(line):
            matches.append(line)
    return matches


def load_datareporting_state(profile_dir: pathlib.Path) -> dict[str, object] | None:
    state_path = profile_dir / "datareporting/state.json"
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_decode_error": True}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture a clean-profile Veil startup network baseline using tshark "
            "and per-process socket snapshots."
        )
    )
    parser.add_argument("browser", help="Path to the built browser binary")
    parser.add_argument("output_dir", help="Directory to store audit artifacts")
    parser.add_argument("--duration", type=int, default=20, help="Capture duration in seconds")
    parser.add_argument("--interface", default="any", help="Capture interface, default: any")
    parser.add_argument(
        "--url",
        default="about:blank",
        help="Initial page to open after startup, default: about:blank",
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=0.25,
        help="Seconds between lsof snapshots, default: 0.25",
    )
    parser.add_argument(
        "--profile-template",
        help="Optional profile directory to copy into the fresh audit profile before launch",
    )
    args = parser.parse_args()

    browser = pathlib.Path(args.browser).resolve()
    if not browser.exists():
        print(f"missing browser binary: {browser}", file=sys.stderr)
        return 2

    if shutil.which("tshark") is None:
        print("tshark is required for network auditing", file=sys.stderr)
        return 2

    if shutil.which("lsof") is None:
        print("lsof is required for per-process socket attribution", file=sys.stderr)
        return 2

    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    env_root = output_dir / "runtime-env"
    profile_dir = output_dir / "profile"
    pcap_path = output_dir / "startup.pcapng"
    packet_tsv = output_dir / "startup-packets.tsv"
    socket_log = output_dir / "browser-sockets.log"
    browser_stdout = output_dir / "browser.stdout.log"
    browser_stderr = output_dir / "browser.stderr.log"
    command_log = output_dir / "commands.json"
    summary_json = output_dir / "summary.json"

    for path in (env_root, profile_dir):
        path.mkdir(parents=True, exist_ok=True)

    if args.profile_template:
        template_dir = pathlib.Path(args.profile_template).resolve()
        if not template_dir.exists():
            print(f"missing profile template: {template_dir}", file=sys.stderr)
            return 2
        shutil.copytree(template_dir, profile_dir, dirs_exist_ok=True)

    runtime_env = os.environ.copy()
    runtime_env.update(
        {
            "HOME": str(env_root / "home"),
            "XDG_CONFIG_HOME": str(env_root / "config"),
            "XDG_CACHE_HOME": str(env_root / "cache"),
            "XDG_DATA_HOME": str(env_root / "data"),
            "MOZ_HEADLESS": "1",
        }
    )
    for name in ("home", "config", "cache", "data"):
        (env_root / name).mkdir(parents=True, exist_ok=True)

    tshark_cmd = [
        "tshark",
        "-i",
        args.interface,
        "-a",
        f"duration:{max(args.duration + 2, 5)}",
        "-f",
        "tcp or udp",
        "-w",
        str(pcap_path),
    ]
    browser_cmd = [
        str(browser),
        "--headless",
        "--no-remote",
        "--profile",
        str(profile_dir),
        args.url,
    ]

    command_log.write_text(
        json.dumps(
            {
                "tshark_cmd": tshark_cmd,
                "browser_cmd": browser_cmd,
                "duration_seconds": args.duration,
                "interface": args.interface,
                "sample_interval_seconds": args.sample_interval,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    tshark_proc = subprocess.Popen(
        tshark_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(1.0)

    browser_start = time.time()
    with browser_stdout.open("wb") as stdout_handle, browser_stderr.open("wb") as stderr_handle:
        browser_proc = subprocess.Popen(
            browser_cmd,
            stdout=stdout_handle,
            stderr=stderr_handle,
            env=runtime_env,
            start_new_session=True,
        )

        with socket_log.open("w", encoding="utf-8") as socket_handle:
            while time.time() - browser_start < args.duration:
                if browser_proc.poll() is not None:
                    break
                socket_handle.write(f"=== {time.time():.6f} ===\n")
                snapshot = subprocess.run(
                    ["lsof", "-nP", "-a", "-p", str(browser_proc.pid), "-i"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                socket_handle.write(snapshot.stdout)
                socket_handle.flush()
                time.sleep(args.sample_interval)

        if browser_proc.poll() is None:
            try:
                os.killpg(browser_proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            browser_exit = browser_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(browser_proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            browser_exit = browser_proc.wait(timeout=10)

    terminate_process(tshark_proc, timeout=10)

    tshark_decode_cmd = [
        "tshark",
        "-r",
        str(pcap_path),
        "-Y",
        "dns or tls or http or tcp.flags.syn==1 or udp",
        "-T",
        "fields",
        "-E",
        "separator=\t",
        "-e",
        "frame.time_epoch",
        "-e",
        "ip.dst",
        "-e",
        "ipv6.dst",
        "-e",
        "tcp.dstport",
        "-e",
        "dns.qry.name",
        "-e",
        "http.host",
        "-e",
        "tls.handshake.extensions_server_name",
    ]
    packet_capture = subprocess.run(
        tshark_decode_cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    packet_tsv.write_text(packet_capture.stdout, encoding="utf-8")

    summary = {
        "browser": str(browser),
        "browser_exit_code": browser_exit,
        "capture_interface": args.interface,
        "duration_seconds": args.duration,
        "profile_dir": str(profile_dir),
        "artifacts": {
            "pcap": str(pcap_path),
            "packet_tsv": str(packet_tsv),
            "socket_log": str(socket_log),
            "browser_stdout": str(browser_stdout),
            "browser_stderr": str(browser_stderr),
            "commands": str(command_log),
        },
        "lsof_remote_endpoints": parse_lsof_remotes(socket_log),
        "packet_destinations": parse_packet_destinations(packet_tsv),
        "profile_pref_matches": collect_profile_pref_matches(profile_dir),
        "datareporting_state": load_datareporting_state(profile_dir),
    }
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
