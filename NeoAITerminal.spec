# -*- mode: python ; coding: utf-8 -*-
"""Small-executable Windows build. Python app is onedir; Node/jsdom stay beside it."""
from pathlib import Path

project = Path.cwd()
datas = [
    (str(project / "web"), "web"),
    (str(project / "lang_fa.json"), "."),
    (str(project / "jsa_jsdom.js"), "."),
]

# PyInstaller's standard hooks collect FastAPI, Starlette, Pydantic, Requests,
# Pillow and their runtime data. Keep only modules imported dynamically by Uvicorn
# and the application. On Windows, secure_store uses native DPAPI, not keyring.
hiddenimports = [
    "duck_cli", "duck_i18n", "duck_voice", "duckai_catalog",
    "web_app", "api_providers", "secure_store", "multipart",
    "uvicorn.logging", "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto", "uvicorn.lifespan.on",
]

a = Analysis(
    [str(project / "neo_launcher.py")],
    pathex=[str(project)],
    binaries=[], datas=datas, hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=[
        "tkinter", "test", "unittest", "pytest", "IPython", "notebook",
        "matplotlib", "scipy", "numpy", "pandas", "keyring", "secretstorage",
        "winrt", "watchfiles", "httptools", "websockets",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Neo AI Terminal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=False,
    name="Neo AI Terminal",
)
