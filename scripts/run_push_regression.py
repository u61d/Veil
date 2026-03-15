#!/usr/bin/env python3

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


def forwarded_args() -> list[str]:
    if "--" in sys.argv:
        index = sys.argv.index("--")
        return sys.argv[index + 1 :]
    return sys.argv[1:]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_srcdir = repo_root / "upstream" / "firefox"
    default_objdir = default_srcdir / "obj-veil"
    parser = argparse.ArgumentParser(
        description=(
            "Run the upstream dom/push mochitest suite against the built Veil "
            "browser using the packaged objdir test harness."
        )
    )
    parser.add_argument(
        "--srcdir",
        default=str(default_srcdir),
        help="Firefox source tree, defaults to upstream/firefox",
    )
    parser.add_argument(
        "--objdir",
        default=str(default_objdir),
        help="Firefox objdir, defaults to upstream/firefox/obj-veil",
    )
    parser.add_argument(
        "--artifact-dir",
        help="Optional directory for mochitest structured logs",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run the browser headlessly",
    )
    return parser.parse_args(forwarded_args())


def ensure_push_test_tree(srcdir: Path, objdir: Path) -> Path:
    packaged_push_parent = objdir / "_tests" / "testing" / "mochitest" / "tests" / "dom" / "push"
    packaged_push_parent.mkdir(parents=True, exist_ok=True)
    packaged_push_dir = packaged_push_parent / "test"
    source_push_dir = srcdir / "dom" / "push" / "test"
    if packaged_push_dir.is_symlink() or packaged_push_dir.exists():
        if packaged_push_dir.resolve() != source_push_dir.resolve():
            packaged_push_dir.unlink()
    if not packaged_push_dir.exists():
        packaged_push_dir.symlink_to(source_push_dir, target_is_directory=True)
    return packaged_push_dir / "mochitest.toml"


def extend_sys_path(srcdir: Path, objdir: Path) -> None:
    test_root = objdir / "_tests"
    paths = [
        srcdir / "python" / "mozterm",
        test_root / "testing" / "mochitest",
        test_root / "reftest",
        test_root / "xpcshell",
        test_root / "modules",
    ]
    paths.extend(
        path for path in sorted((test_root / "mozbase").iterdir()) if path.is_dir()
    )
    sys.path[:0] = [str(path) for path in paths if path.exists()]


def build_runtests_argv(
    *,
    srcdir: Path,
    objdir: Path,
    manifest: Path,
    artifact_dir: Path | None,
    headless: bool,
) -> list[str]:
    dist_bin = objdir / "dist" / "bin"
    argv = [
        "runtests.py",
        "--appname",
        str(dist_bin / "firefox"),
        "--xre-path",
        str(dist_bin),
        "--utility-path",
        str(dist_bin),
        "--certificate-path",
        str(srcdir / "build" / "pgo" / "certs"),
        "--manifest",
        str(manifest),
    ]
    if headless:
        argv.append("--headless")
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        argv.extend(
            [
                "--log-mach",
                str(artifact_dir / "dom_push_suite.mach.log"),
                "--log-raw",
                str(artifact_dir / "dom_push_suite.raw.log"),
            ]
        )
    return argv


def main() -> int:
    args = parse_args()
    srcdir = Path(args.srcdir).resolve()
    objdir = Path(args.objdir).resolve()
    manifest = ensure_push_test_tree(srcdir, objdir)
    extend_sys_path(srcdir, objdir)
    artifact_dir = Path(args.artifact_dir).resolve() if args.artifact_dir else None
    sys.argv = build_runtests_argv(
        srcdir=srcdir,
        objdir=objdir,
        manifest=manifest,
        artifact_dir=artifact_dir,
        headless=args.headless,
    )
    runpy.run_path(
        str(objdir / "_tests" / "testing" / "mochitest" / "runtests.py"),
        run_name="__main__",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
