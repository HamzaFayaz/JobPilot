"""Writable paths for packaged Search Helper (.exe) vs dev `python main.py`."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def worker_data_dir() -> Path:
    """Config, lock file, and debug snapshots — always user-writable."""
    override = os.environ.get("JOBPILOT_WORKER_DATA_DIR", "").strip()
    if override:
        path = Path(override)
    elif is_frozen():
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        path = Path(base) / "JobPilot" / "SearchHelper"
    else:
        path = _PACKAGE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def repo_root() -> Path:
    """Import root for `worker` package (repo root in dev, _MEIPASS when frozen)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", _PACKAGE_DIR.parent))
    return _PACKAGE_DIR.parent
