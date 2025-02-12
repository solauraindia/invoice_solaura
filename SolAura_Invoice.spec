# -*- mode: python ; coding: utf-8 -*-
import os

icon_path = os.path.join('src', 'public', 'invoice.ico')
logo_path = os.path.join('src', 'public', 'solaura_logo.jpg')

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('.env', './'),
        (logo_path, os.path.join('src', 'public')),
        (icon_path, os.path.join('src', 'public'))
    ],
    hiddenimports=[],
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
    a.datas,
    [],
    name='SolAura_Invoice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path
)
