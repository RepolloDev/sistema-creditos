# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
BASE_DIR = Path.cwd()

datas = [
    (str(BASE_DIR / 'templates'), 'templates'),
    (str(BASE_DIR / 'staticfiles'), 'staticfiles'),
    (str(BASE_DIR / 'database' / 'db.sqlite3'), 'database'),
    (str(BASE_DIR / 'apps'), 'apps'),
]

hiddenimports = [
    'waitress',
    'whitenoise',
    'whitenoise.middleware',
    'whitenoise.storage',
    'pystray',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'django',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
    'clientes',
    'solicitudes',
    'evaluacion',
    'creditos',
    'pagos',
    'integraciones',
    'config',
]

a = Analysis(
    ['run_app.py'],
    pathex=[str(BASE_DIR), str(BASE_DIR / 'apps')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['debug_toolbar'],
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
    name='sis-creditos',
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
