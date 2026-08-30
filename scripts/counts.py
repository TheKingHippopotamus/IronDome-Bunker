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
defines, asks the package what version it is, and prints the answers as JSON.

The site lives in its own repository -- TheKingHippopotamus/IronDome-Bunker- --
and imports the result as ``src/data/counts.json``. Because that checkout is
somewhere only you know, the destination is always given explicitly; there is
no default path to go stale.

Usage::

    python scripts/counts.py                          # print the JSON
    python scripts/counts.py --out PATH               # write it to PATH
    python scripts/counts.py --check PATH             # exit 1 if PATH is stale

Run it against the site checkout before ``npm run build``::

    python scripts/counts.py --out ../IronDome-Bunker-/src/data/counts.json
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--out",
        metavar="PATH",
        help="write the JSON to PATH (in the site checkout); default is stdout",
    )
    group.add_argument(
        "--check",
        metavar="PATH",
        help="do not write; exit non-zero if the JSON at PATH is stale",
    )
    args = parser.parse_args()

    counts = collect()
    serialised = json.dumps(counts, indent=2) + "\n"

    if args.check:
        try:
            with open(args.check, encoding="utf-8") as handle:
                committed = json.load(handle)
        except (OSError, ValueError):
            committed = None
        if committed != counts:
            print(f"stale: {args.check}\n  committed {committed}\n  actual    {counts}")
            return 1
        print(f"current: {counts}")
        return 0

    if not args.out:
        sys.stdout.write(serialised)
        return 0

    parent = os.path.dirname(os.path.abspath(args.out))
    if not os.path.isdir(parent):
        raise SystemExit(
            f"no such directory: {parent}\n"
            "Point --out at the site checkout, e.g. "
            "../IronDome-Bunker-/src/data/counts.json"
        )
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(serialised)
    print(f"wrote {args.out}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
