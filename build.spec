# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build specification for OSINT-Nexus
Run with: pyinstaller build.spec
"""

import sys
from pathlib import Path

block_cipher = None
root_dir = Path(SPECPATH)

# Handle optional assets directory
assets_dir = root_dir / 'assets'
datas = []
if assets_dir.exists():
    datas.append((str(assets_dir), 'assets'))

a = Analysis(
    [str(root_dir / 'src' / 'main.py')],
    pathex=[str(root_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'pyqtgraph',
        'networkx',
        'aiohttp',
        'requests',
        'phonenumbers',
        'whois',
        'dns.resolver',
        'bs4',
        'lxml',
        'shodan',
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
    name='osint-nexus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root_dir / 'assets' / 'app_icon.ico') if (root_dir / 'assets' / 'app_icon.ico').exists() else None,
)
