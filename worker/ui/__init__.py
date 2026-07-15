"""Search Helper desktop UI assets and widgets."""

from __future__ import annotations

import sys
from pathlib import Path

from worker.runtime_paths import is_frozen

_PACKAGE_DIR = Path(__file__).resolve().parent


def ui_dir() -> Path:
    if is_frozen():
        base = Path(getattr(sys, "_MEIPASS", _PACKAGE_DIR.parent))
        bundled = base / "worker" / "ui"
        if bundled.is_dir():
            return bundled
    return _PACKAGE_DIR


def asset_path(name: str) -> Path:
    return ui_dir() / "assets" / name


def load_stylesheet() -> str:
    path = ui_dir() / "styles.qss"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""
