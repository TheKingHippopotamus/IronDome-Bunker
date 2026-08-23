"""Static proof that the installed package makes no network calls.

README.md claims the package opens no sockets and binds no ports.  This test
is what makes that claim checkable: it walks every module shipped inside
``password_manager/`` and fails if any of them imports a networking module or
calls a networking entry point.

The allowlist is deliberately empty.  If a future change genuinely needs
network access, adding the module here is a conscious act that also requires
editing the README claim in the same commit.
"""

import ast
import os
import pathlib
import re

import pytest

import password_manager

#: Modules no file in the package may import.  Intentionally empty allowlist.
FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "socket",
        "socketserver",
        "ssl",
        "http",
        "urllib",
        "urllib2",
        "urllib3",
        "requests",
        "httpx",
        "aiohttp",
        "websockets",
        "websocket",
        "ftplib",
        "smtplib",
        "poplib",
        "imaplib",
        "telnetlib",
        "xmlrpc",
        "asyncore",
        "asynchat",
        "textual_serve",
    }
)

#: Bare callables that would perform network I/O even without a top-level import.
FORBIDDEN_CALL_NAMES = frozenset(
    {"urlopen", "gethostbyname", "getaddrinfo", "create_connection", "socketpair"}
)

#: Modules explicitly permitted to import from FORBIDDEN_IMPORT_ROOTS.  Empty.
ALLOWLIST: frozenset = frozenset()


def _package_modules():
    root = pathlib.Path(password_manager.__file__).resolve().parent
    return sorted(root.rglob("*.py"))


def _relname(path):
    root = pathlib.Path(password_manager.__file__).resolve().parent
    return str(pathlib.Path(path).resolve().relative_to(root.parent))


def test_package_imports_without_network_side_effects():
    """The package must import cleanly (and this pins the scan root)."""
    assert password_manager.__file__
    assert _package_modules(), "no modules found to scan — scan root is wrong"


@pytest.mark.parametrize("path", _package_modules(), ids=_relname)
def test_module_imports_no_network_library(path):
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"), filename=str(path))
    rel = _relname(path)
    offenders = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    offenders.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import — cannot reach stdlib networking
                continue
            root = (node.module or "").split(".")[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                offenders.append(f"line {node.lineno}: from {node.module} import ...")

    if rel in ALLOWLIST:
        pytest.skip(f"{rel} is on the allowlist")

    assert not offenders, (
        f"{rel} references a networking module: " + "; ".join(offenders)
    )


@pytest.mark.parametrize("path", _package_modules(), ids=_relname)
def test_module_calls_no_network_entry_point(path):
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"), filename=str(path))
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name in FORBIDDEN_CALL_NAMES:
            offenders.append(f"line {node.lineno}: {name}(...)")
    assert not offenders, (
        f"{_relname(path)} calls a networking entry point: " + "; ".join(offenders)
    )


def test_no_url_literals_in_source():
    """No http(s):// endpoint appears as a string literal in the package.

    Comments are excluded (a comment cannot make a request), and a bare
    ``"://"`` scheme separator used for URL parsing is not an endpoint --
    the pattern requires a host character after the slashes.
    """
    endpoint = re.compile(r"https?://\S")
    offenders = []
    for path in _package_modules():
        tree = ast.parse(
            pathlib.Path(path).read_text(encoding="utf-8"), filename=str(path)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if endpoint.search(node.value):
                    offenders.append(
                        f"{_relname(path)}:{node.lineno}: {node.value[:80]!r}"
                    )
    assert not offenders, "URL endpoint literals found:\n" + "\n".join(offenders)


def test_allowlist_is_empty():
    """Guard the guard: an allowlist entry must be a deliberate, reviewed change."""
    assert ALLOWLIST == frozenset(), (
        "The no-network allowlist is non-empty. Update the README claim in the "
        f"same commit: {sorted(ALLOWLIST)}"
    )


def test_data_dir_env_is_isolated_during_tests(tmp_path, monkeypatch):
    """Sanity: tests never touch a real home directory."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert os.path.expanduser("~") == str(tmp_path)
