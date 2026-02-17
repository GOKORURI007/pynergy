# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# 定义路径
pro_root = os.path.abspath(".")
client_src = os.path.join(pro_root, "packages/pynergy_client/src")
protocol_src = os.path.join(pro_root, "packages/pynergy_protocol/src")

a = Analysis(
    # 指向你的入口文件
    ['main.py'],
    pathex=[client_src, protocol_src], # 将两个子包的 src 都加入路径
    binaries=[],
    datas=[
        # 包含翻译文件：(源路径, 目标包内路径)
        ('packages/pynergy_client/src/pynergy_client/locales', 'pynergy_client/locales'),
        ('packages/pynergy_client/pyproject.toml', '.'),
    ],
    hiddenimports=[
        'pynergy_protocol',
        'typer',
        'cryptography',
        'rich._unicode_data.unicode17-0-0'
        # 如果有动态导入的模块，在这里列出
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
    name='pynergy-client', # 生成的可执行文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # 设为 True 以便看到命令行输出
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
