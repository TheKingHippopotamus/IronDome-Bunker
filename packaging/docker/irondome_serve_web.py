#!/usr/bin/env python3
"""Serve IronDome TUI in the browser via textual-serve (Textual WebDriver).

When the server binds to 0.0.0.0, textual-serve would otherwise emit asset URLs
like http://0.0.0.0:8000/... which browsers cannot load. Set IRONDOME_PUBLIC_URL
to the URL you open in the browser (scheme + host + published port).
"""
from __future__ import annotations

import os
from pathlib import Path

from textual_serve.server import Server

# Custom templates live next to this script so they are baked into the image.
_THIS_DIR = Path(__file__).parent
_CUSTOM_TEMPLATES = _THIS_DIR / "templates"


def _binds_all_interfaces(host: str) -> bool:
    return host in ("0.0.0.0", "::", "[::]")


def main() -> None:
    host = os.environ.get("IRONDOME_SERVE_HOST", "0.0.0.0")
    port = int(os.environ.get("IRONDOME_SERVE_PORT", "8000"))
    title = os.environ.get("IRONDOME_SERVE_TITLE", "IronDome")
    command = os.environ.get("IRONDOME_SERVE_COMMAND", "irondome")

    public_url = os.environ.get("IRONDOME_PUBLIC_URL", "").strip() or None
    if public_url is None and _binds_all_interfaces(host):
        # Same-machine Docker default; override IRONDOME_PUBLIC_URL if the host port differs.
        public_url = f"http://127.0.0.1:{port}"

    kwargs: dict = {
        "command": command,
        "host": host,
        "port": port,
        "title": title,
    }
    if public_url:
        kwargs["public_url"] = public_url
    if _CUSTOM_TEMPLATES.is_dir():
        kwargs["templates_path"] = str(_CUSTOM_TEMPLATES)

    Server(**kwargs).serve()


if __name__ == "__main__":
    main()
