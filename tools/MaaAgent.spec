# -*- mode: python ; coding: utf-8 -*-
"""
MaaAgent PyInstaller 配置文件
用于打包 Python Agent 为单可执行文件

使用方法:
    cd 到项目根目录，然后执行:
    pyinstaller tools/MaaAgent.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

# 获取项目根目录(spec 文件在 tools/ 下,需要返回上一级)
spec_root = os.path.dirname(os.path.abspath(SPECPATH))

# 收集 pywin32 的所有内容
pywin32_datas, pywin32_binaries, pywin32_hiddenimports = collect_all('pywin32')

# 收集 maa 包的所有内容(包括 DLL 和子模块)
maa_datas, maa_binaries, maa_hiddenimports = collect_all('maa')

block_cipher = None

a = Analysis(
    [os.path.join(spec_root, 'agent', 'main.py')],
    pathex=[],
    binaries=pywin32_binaries + maa_binaries,
    datas=[
        (os.path.join(spec_root, 'agent', 'config'), 'config'),
        (os.path.join(spec_root, 'agent', 'postmessage'), 'postmessage'),
    ] + pywin32_datas + maa_datas,
    hiddenimports=[
        'win32timezone',
        'win32api',
        'win32con',
        'win32gui',
        'maa.agent',
        'maa.agent.agent_server',
    ] + pywin32_hiddenimports + maa_hiddenimports,
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
    name='MaaAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台窗口以显示日志
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可选: 添加图标文件路径
)
