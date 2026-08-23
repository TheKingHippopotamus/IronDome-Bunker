#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate the numbers the website prints, from the thing they describe.

The landing page carries a spec table with no adjectives in it -- test count,
screen count, version. Written by hand, those numbers are correct on the day
the page is written and drift the moment a test is added. The published 3.2.1
page said 143 tests against a suite that collected 144, which is a small error
of exactly the kind a page built on "check it against the source" cannot
afford.

So the page does not get to hold an opinion about them. This script asks the
suite how many tests it collects, asks the TUI package how many screens it
defines, asks the package what version it is, and writes the answers to
``website/src/data/counts.json``. The Astro page imports that file.

Usage::

    python scripts/counts.py            # write website/src/data/counts.json
    python scripts/counts.py --check    # exit 1 if the file is out of date

Run it in the same pass that builds the site, before ``npm run build``.
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "website", "src", "data", "counts.json")
SCREENS_DIR = os.path.join(ROOT, "password_manager", "tui", "screens")

#: Textual base classes that make a class a screen the user can be looking at.
SCREEN_BASES = {"Screen", "ModalScreen"}


def collect_tests():
    """Ask pytest what it collects. Returns (total, {file: count}).

    The suite is the authority on its own size; nothing here counts ``def
    test_`` lines. The per-file map may come back empty on a pytest whose
    ``-q`` output is only a summary line -- the total is always available.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit("pytest --collect-only failed; refusing to guess a number")

    # Three shapes, because -q --collect-only has not printed the same thing
    # across pytest versions. Take whichever the installed one produced.

    # 1. One line per file: "tests/test_nuke.py: 12".
    per_file = re.findall(r"^(\S+\.py):\s*(\d+)\s*$", result.stdout, re.MULTILINE)
    if per_file:
        files = {os.path.basename(path): int(n) for path, n in per_file}
        return sum(files.values()), files

    # 2. One line per test: "tests/test_nuke.py::test_thing".
    node_ids = [ln.strip() for ln in result.stdout.splitlines() if "::" in ln]
    if node_ids:
        files = {}
        for node_id in node_ids:
            name = os.path.basename(node_id.split("::", 1)[0])
            files[name] = files.get(name, 0) + 1
        return len(node_ids), files

    # 3. A summary line only: "157 tests collected in 0.42s".
    summary = re.search(r"^(\d+)\s+tests?\s+collected", result.stdout, re.MULTILINE)
    if summary:
        return int(summary.group(1)), {}

    sys.stderr.write(result.stdout)
    raise SystemExit("could not read a test count out of pytest's output")


def count_screens():
    """Number of Screen/ModalScreen subclasses defined under tui/screens/.

    Parsed rather than imported: importing the TUI pulls in Textual and, on a
    headless box, a terminal that is not there.
    """
    total = 0
    for name in sorted(os.listdir(SCREENS_DIR)):
        if not name.endswith(".py") or name == "__init__.py":
            continue
        with open(os.path.join(SCREENS_DIR, name), encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {_base_name(b) for b in node.bases}
            if bases & SCREEN_BASES:
                total += 1
    return total


def _base_name(node):
    """Name of a base class expression: Screen, textual.Screen, ModalScreen[bool]."""
    if isinstance(node, ast.Subscript):  # ModalScreen[bool]
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def read_version():
    """The version in password_manager/__init__.py, read without importing it."""
    init = os.path.join(ROOT, "password_manager", "__init__.py")
    with open(init, encoding="utf-8") as handle:
        match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', handle.read(), re.M)
    if not match:
        raise SystemExit("no __version__ in password_manager/__init__.py")
    return match.group(1)


def collect():
    total, files = collect_tests()
    return {
        "tests": total,
        "screens": count_screens(),
        "version": read_version(),
        # Per-file breakdown, because the page prints one.
        "files": dict(sorted(files.items())),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit non-zero if the committed counts are stale",
    )
    args = parser.parse_args()

    counts = collect()
    serialised = json.dumps(counts, indent=2) + "\n"

    if args.check:
        try:
            with open(OUT_PATH, encoding="utf-8") as handle:
                committed = json.load(handle)
        except (OSError, ValueError):
            committed = None
        if committed != counts:
            print(f"stale: {OUT_PATH}\n  committed {committed}\n  actual    {counts}")
            return 1
        print(f"current: {counts}")
        return 0

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(serialised)
    print(f"wrote {os.path.relpath(OUT_PATH, ROOT)}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
