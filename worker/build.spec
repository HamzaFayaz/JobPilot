# PyInstaller spec — run from worker/:  ..\.venv\Scripts\pyinstaller.exe build.spec
# Output: worker/dist/JobPilot-SearchHelper.exe

import sys
from pathlib import Path

block_cipher = None

spec_dir = Path(SPECPATH)
repo_root = spec_dir.parent

a = Analysis(
    ["app_entry.py"],
    pathex=[str(repo_root), str(spec_dir)],
    binaries=[],
    datas=[
        (str(spec_dir / "ui" / "styles.qss"), str(Path("worker") / "ui")),
        (str(spec_dir / "ui" / "assets" / "icon.ico"), str(Path("worker") / "ui" / "assets")),
        (str(spec_dir / "ui" / "assets" / "icon.png"), str(Path("worker") / "ui" / "assets")),
    ],
    hiddenimports=[
        "worker",
        "worker.main",
        "worker.app_entry",
        "worker.launcher",
        "worker.ui",
        "worker.ui.widgets",
        "worker.ui.settings_panel",
        "worker.ui.logs_window",
        "worker.local_config",
        "worker.runtime_paths",
        "worker.config",
        "worker.api_client",
        "worker.browser_client",
        "worker.agent_loop",
        "worker.parse",
        "worker.prompts",
        "worker.models",
        "worker.linkedin_urls",
        "worker.run_metrics",
        "worker.snapshot_compress",
        "worker.snapshot_store",
        "worker.webbridge_scroll",
        "worker.webbridge_tools",
        "worker.providers",
        "worker.providers.webbridge",
        "pydantic",
        "pydantic_settings",
        "pydantic.deprecated.decorator",
        "openai",
        "httpx",
        "httpcore",
        "anyio",
        "certifi",
        "dotenv",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="JobPilot-SearchHelper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
