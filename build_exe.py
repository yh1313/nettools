# -*- mode: python ; coding: utf-8 -*-
# NetTools PyInstaller 打包配置 - 优化版

from PyInstaller.__main__ import run as pyi_run

opts = [
    'NetTools.spec',       # 使用 spec 文件（含版本信息）
    '--clean',             # 清理缓存
    '--noconfirm',         # 不询问确认
    '--log-level=INFO',
]

if __name__ == '__main__':
    pyi_run(opts)
