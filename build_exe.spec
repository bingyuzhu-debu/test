# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 收集backend目录下的所有Python文件
backend_files = [
    ('backend/main.py', 'backend'),
    ('backend/database.py', 'backend'),
    ('backend/models.py', 'backend'),
    ('backend/services.py', 'backend'),
    ('backend/utils.py', 'backend'),
    ('backend/requirements.txt', 'backend'),
]

# 收集frontend目录
frontend_files = [
    ('frontend/*', 'frontend'),
    ('frontend/assets/*', 'frontend/assets'),
]

# 收集必要的目录
data_dirs = [
    ('backend/uploads', 'backend/uploads'),
    ('backend/outputs', 'backend/outputs'),
    ('底表文件夹', '底表文件夹'),
]

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=backend_files + frontend_files + data_dirs,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'sqlalchemy',
        'xlrd',
        'xlwt',
        'reportlab',
        'backend.main',
        'backend.database',
        'backend.models',
        'backend.services',
        'backend.utils',
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
    name='银行对账单生成系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口，方便查看日志
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加自定义图标
)
