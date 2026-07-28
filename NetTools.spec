# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('ttkbootstrap')


a = Analysis(
    ['nettools.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'IPython',
        'ipython',
        'ipython_genutils',
        'jedi',
        'paramiko',
        'zmq',
        'zstandard',
        'bcrypt',
        'nacl',
        'cryptography',
        'traitlets',
        'jupyter_client',
        'jupyter_core',
        'parso',
        'pygments',
        'prompt_toolkit',
        'pexpect',
        'ptyprocess',
        'wcwidth',
        'stack_data',
        'asttokens',
        'executing',
        'pure_eval',
        'matplotlib_inline',
        'decorator',
    ],
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
    name='NetTools',
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
    uac_admin=True,
)
