# -*- mode: python ; coding: utf-8 -*-
# NetTools PyInstaller 打包配置 - 安全优化版
# 使用 onedir 模式，大幅降低安全软件误报率

import sys
import os

block_cipher = None

# 版本信息（Windows 文件属性中显示，减少误报）
version_info = {
    'CompanyName': 'NetTools',
    'FileDescription': 'NetTools - Network Engineer Toolbox',
    'FileVersion': '1.2.0.0',
    'InternalName': 'NetTools',
    'LegalCopyright': 'MIT License - Free Open Source Software',
    'OriginalFilename': 'NetTools.exe',
    'ProductName': 'NetTools Network Toolbox',
    'ProductVersion': '1.2.0.0',
}

a = Analysis(
    ['nettools.py'],
    pathex=[],
    binaries=[],
    datas=[('tools.py', '.')],
    hiddenimports=[
        'ping3',
        'dns.resolver',
        'dns.rdatatype',
        'dns.rdataclass',
        'dns.message',
        'dns.query',
        'dns.name',
        'dns.rcode',
        'dns.exception',
        'requests',
        'urllib3',
        'certifi',
        'chardet',
        'idna',
        'http.cookies',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'pillow',
        'PyQt5', 'PySide2', 'PySide6', 'wx',
        'tkinter.test', 'unittest', 'pydoc',
        'lib2to3', 'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 使用 onedir 模式（目录分发），比 onefile 模式安全得多
# 安全软件对 onedir 模式的误报率远低于 onefile
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NetTools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_info=version_info,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='NetTools',
)
