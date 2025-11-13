# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\James\\AppData\\Local\\Programs\\Python\\Python312\\Lib'],
    binaries=[],
    datas=[('src', 'src'), ('resources', 'resources')],
    hiddenimports=[
        # Core Python modules
        'platform', 'os', 'sys', 'inspect', 'functools', 'traceback', 'types',
        'warnings', 'weakref', 'gc', 'atexit', 'signal',
        
        # GUI - tkinter
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
        'tkinter.scrolledtext', 'tkinter.font', 'tkinter.colorchooser',
        '_tkinter',
        
        # Data structures and types
        'json', 'pathlib', 'collections', 'collections.abc', 'datetime', 're', 
        'io', 'struct', 'array', 'enum', 'dataclasses',
        
        # Database
        'sqlite3',
        
        # File/Path operations
        'csv', 'tempfile', 'shutil', 'glob', 'fnmatch', 'codecs',
        
        # XML/HTML
        'xml', 'xml.etree', 'xml.etree.ElementTree',
        
        # Logging
        'logging', 'logging.handlers', 'logging.config',
        
        # Threading/Concurrency
        'threading', 'concurrent', 'concurrent.futures', 'multiprocessing',
        'queue', 'asyncio',
        
        # Utilities
        'time', 'math', 'random', 'string', 'itertools', 'operator',
        'contextlib', 'copy', 'pickle', 'base64', 'hashlib', 'secrets',
        'uuid', 'decimal', 'fractions',
        
        # System/Process
        'subprocess', 'argparse', 'getopt',
        
        # Import utilities
        'importlib', 'importlib.util', 'importlib.machinery', 'pkgutil',
        
        # Networking (if needed)
        'socket', 'ssl', 'http', 'http.client', 'urllib', 'urllib.parse',
        
        # Error handling
        'errno', 'traceback',
        
        # Audio modules
        'wave', 'audioop', 'chunk', 'sunau', 'aifc', 'sndhdr',
        
        # Third-party packages
        'filelock',
        'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageDraw', 'PIL.ImageFont',
        'pygame', 'pygame.mixer', 'pygame.locals',
        'mutagen', 'mutagen.mp3', 'mutagen.id3', 'mutagen.flac', 'mutagen.oggvorbis',
        'pyperclip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
    optimize=0,
)

# Collect tkinter DLLs
import sys
import os
tkinter_path = os.path.join(sys.base_prefix, 'DLLs')
if os.path.exists(tkinter_path):
    for dll in ['tcl86t.dll', 'tk86t.dll', '_tkinter.pyd']:
        dll_path = os.path.join(tkinter_path, dll)
        if os.path.exists(dll_path):
            a.binaries.append((dll, dll_path, 'BINARY'))

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MusikArchiveViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if os.path.exists('resources/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MusikArchiveViewer',
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)