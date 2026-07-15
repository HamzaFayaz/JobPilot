"""JobPilot Search Helper — PyInstaller entry point (GUI + internal worker mode)."""

from __future__ import annotations

import sys

from worker.runtime_paths import repo_root


def _bootstrap_imports() -> None:
    root = repo_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _run_worker() -> None:
    from worker.local_config import apply_config_to_environ, load_config
    from worker.main import main

    apply_config_to_environ(load_config())
    main()


def _run_gui() -> None:
    from worker.launcher import run_launcher

    run_launcher()


def run() -> None:
    _bootstrap_imports()
    if "--worker-internal" in sys.argv:
        _run_worker()
        return
    _run_gui()


if __name__ == "__main__":
    run()
