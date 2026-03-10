# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path.cwd()
hiddenimports = (
    collect_submodules("fastapi")
    + collect_submodules("starlette")
    + collect_submodules("uvicorn")
    + collect_submodules("jinja2")
)
datas = [
    (str(project_root / "pc_monitor" / "templates"), "pc_monitor/templates"),
    (str(project_root / "pc_monitor" / "static"), "pc_monitor/static"),
]


a = Analysis(
    ["run.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="PCMonitorServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
