#!/usr/bin/env python3
"""Validate local toolchain against lock manifest."""

from __future__ import annotations

import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "toolchain.lock.toml"


def _run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def _normalize(v: str) -> str:
    m = re.search(r"\d+(?:\.\d+)+", v)
    return m.group(0) if m else v.strip()


def main() -> None:
    lock = tomllib.loads(LOCK_PATH.read_text())
    errors: list[str] = []

    expected_py = str(lock["python"]["version"])
    actual_py = _normalize(sys.version.split()[0])
    if actual_py != expected_py:
        errors.append(f"python mismatch: expected {expected_py}, got {actual_py}")

    expected_prime = str(lock["cli"]["prime"])
    actual_prime = _normalize(_run(["prime", "--version"]))
    if actual_prime != expected_prime:
        errors.append(f"prime mismatch: expected {expected_prime}, got {actual_prime}")

    for pkg, expected in lock.get("packages", {}).items():
        actual = importlib.metadata.version(pkg)
        if actual != str(expected):
            errors.append(f"{pkg} mismatch: expected {expected}, got {actual}")

    if errors:
        print("TOOLCHAIN CHECK FAILED")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)

    print("TOOLCHAIN CHECK PASSED")


if __name__ == "__main__":
    main()
