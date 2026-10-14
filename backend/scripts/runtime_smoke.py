"""Offline, credential-free smoke gate for the built backend image."""

from __future__ import annotations

import importlib
import json
import shutil
import sqlite3
import ssl
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    modules = (
        "fastapi", "uvicorn", "httpx", "websockets", "multipart",
        "sqlalchemy", "psycopg2", "kubernetes", "requests", "celery",
        "kafka", "argon2", "cryptography", "yaml",
        "app.auth.oauth", "app.services.provisioning",
        "app.adapters.openshift.cleanup", "app.adapters.openshift.provisioning",
    )
    for module in modules:
        importlib.import_module(module)
    if not ssl.create_default_context().get_ca_certs():
        raise RuntimeError("Runtime lost its default certificate trust store")
    with sqlite3.connect(":memory:") as database:
        assert database.execute("select 1").fetchone() == (1,)
    with tempfile.TemporaryDirectory() as directory:
        probe = Path(directory) / "probe"
        probe.write_text("ok", encoding="utf-8")
        assert probe.read_text(encoding="utf-8") == "ok"
    commands = (
        ["oc", "version", "--client=true", "-o", "json"],
        ["helm", "version", "--short"],
        ["git", "--version"],
        ["curl", "--version"],
        ["openssl", "version"],
    )
    for command in commands:
        if not shutil.which(command[0]):
            raise RuntimeError(f"Missing runtime tool: {command[0]}")
        subprocess.run(command, check=True, capture_output=True, timeout=30)
    installed = subprocess.run(
        ["rpm", "-qa", "--qf", "%{NAME}\\n"],
        check=True, capture_output=True, text=True, timeout=30,
    )
    forbidden = {
        "httpd", "httpd-core", "httpd-devel", "httpd-filesystem", "httpd-tools",
        "mod_ldap", "mod_lua", "mod_session", "mod_ssl", "gd", "gd-devel",
        "kernel-headers", "python3.11-devel", "expat-devel", "libblkid-devel",
        "libmount-devel", "go-srpm-macros", "qt5-srpm-macros",
        "emacs-filesystem", "vim-filesystem", "vim-minimal", "libX11-devel",
    }
    remaining = forbidden.intersection(installed.stdout.splitlines())
    if remaining:
        raise RuntimeError(f"Unused runtime packages remain: {sorted(remaining)}")
    for directory in ("/opt/catalog", "/opt/deploy", "/opt/config"):
        if not Path(directory).is_dir():
            raise RuntimeError(f"Missing platform content: {directory}")
    print(json.dumps({
        "status": "PASS", "network": "not-used", "modules": len(modules),
        "tools": [command[0] for command in commands], "unused_packages": 0,
    }))


if __name__ == "__main__":
    main()
