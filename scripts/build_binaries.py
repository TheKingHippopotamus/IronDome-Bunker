#!/usr/bin/env python3
"""
Build standalone IronDome executables with PyInstaller.

Run from the repository root after installing the package and PyInstaller:

    pip install -e ".[binary]"
    python scripts/build_binaries.py

PyInstaller does not cross-compile; use GitHub Actions (build-binaries.yml)
to produce Windows, Linux, and macOS artifacts from one push or manual run.

Binaries go to dist-artifacts/ by default so ./dist stays for setuptools (wheels/sdists).
Upload to PyPI with: twine upload dist/*.whl dist/*.tar.gz
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packaging" / "pyinstaller"
# Keep PyInstaller output out of ./dist — that folder is for `python -m build` (wheels/sdists).
# `twine upload dist/*` fails on bare executables (InvalidDistribution: missing Name, Version).
DEFAULT_BINARY_DIST = ROOT / "dist-artifacts"


def _pyinstaller_base_args(onefile: bool, bundle_tui_stack: bool) -> list[str]:
    """bundle_tui_stack: True for the Textual TUI (collects textual, rich, all password_manager)."""
    out: list[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        *(["--onefile"] if onefile else ["--onedir"]),
        "--console",
    ]
    if bundle_tui_stack:
        out.extend(
            [
                "--collect-all",
                "textual",
                "--collect-all",
                "rich",
                "--collect-submodules",
                "password_manager",
            ]
        )
    return out


def _run(
    name: str,
    script: Path,
    onefile: bool,
    dist_dir: Path | None,
    *,
    bundle_tui_stack: bool,
) -> None:
    args = _pyinstaller_base_args(onefile, bundle_tui_stack)
    if dist_dir is not None:
        args.extend(["--distpath", str(dist_dir)])
        args.extend(["--workpath", str(dist_dir / "_build" / name / "work")])
        args.extend(["--specpath", str(dist_dir / "_build" / name)])
    args.extend(["--name", name, str(script)])
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build IronDome PyInstaller binaries.")
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Use onedir instead of onefile (faster startup, larger folder).",
    )
    parser.add_argument(
        "--dist",
        type=Path,
        default=None,
        help=f"PyInstaller output directory (default: {DEFAULT_BINARY_DIST.name}/).",
    )
    args = parser.parse_args()
    onefile = not args.onedir
    dist = (args.dist.resolve() if args.dist else DEFAULT_BINARY_DIST)
    dist.mkdir(parents=True, exist_ok=True)

    targets: tuple[tuple[str, str, bool], ...] = (
        ("irondome", "irondome_tui.py", True),
        ("irondome-cli", "irondome_cli.py", False),
        ("bunker", "bunker_cli.py", False),
    )
    for exe_name, script_name, bundle_tui in targets:
        script = PACK / script_name
        if not script.is_file():
            raise SystemExit(f"Missing entry script: {script}")
        _run(
            exe_name,
            script,
            onefile,
            dist,
            bundle_tui_stack=bundle_tui,
        )

    if sys.platform == "win32":
        print("Built:", dist / "irondome.exe", dist / "irondome-cli.exe", dist / "bunker.exe", sep="\n  ")
    else:
        print("Built:", dist / "irondome", dist / "irondome-cli", dist / "bunker", sep="\n  ")


if __name__ == "__main__":
    main()
