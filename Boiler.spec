# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('bin/ffmpeg', 'bin')]
binaries = []
hiddenimports = ['pyobjc', 'objc']
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=binaries,
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
    [],
    exclude_binaries=True,
    name='Boiler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Boiler',
)
app = BUNDLE(
    coll,
    name='Boiler.app',
    icon='ZohoBoil.icns',
    bundle_identifier='com.jejestudios.boiler',
    info_plist={
        'CFBundleName': 'Boiler',
        'CFBundleDisplayName': 'Boiler',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'LSMinimumSystemVersion': '12.0',
        'NSHighResolutionCapable': True,
        # Without these, macOS silently denies access to the folders people
        # actually save into instead of showing the permission prompt.
        'NSDownloadsFolderUsageDescription':
            'Boiler saves your finished videos to Downloads.',
        'NSDesktopFolderUsageDescription':
            'Boiler reads videos from and saves finished videos to your Desktop.',
        'NSDocumentsFolderUsageDescription':
            'Boiler reads videos from and saves finished videos to Documents.',
        'NSRemovableVolumesUsageDescription':
            'Boiler reads videos stored on external drives.',
    },
)
