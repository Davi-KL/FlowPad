# flowpad.spec
# Arquivo de configuração do PyInstaller para gerar o .exe do FlowPad
# Execute com: pyinstaller flowpad.spec

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pystray._win32',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'plyer.platforms.win.notification',
        'PIL._tkinter_finder',
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
    name='FlowPad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # FALSE = sem janela de terminal ao iniciar
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # Descomente quando tiver o ícone
)
