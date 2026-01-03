# -*- mode: python ; coding: utf-8 -*-

"""
Weather ONEDIR Spec - Met SSL support voor Python 3.13
Versie: 1.0.0
"""

import sys
import os
import glob

print("="*60)
print("Weather BUILD - SSL DLL DETECTION")
print("="*60)

# Python paths
python_path = sys.base_prefix if hasattr(sys, 'base_prefix') else sys.prefix
python_exe_dir = os.path.dirname(sys.executable)

print(f"Python path: {python_path}")
print(f"Python exe dir: {python_exe_dir}")

# Python DLL
python_dll = None
dll_name = f"python{sys.version_info.major}{sys.version_info.minor}.dll"

dll_locations = [
    os.path.join(python_path, dll_name),
    os.path.join(python_exe_dir, dll_name),
    os.path.join('C:\\Windows\\System32', dll_name),
]

for loc in dll_locations:
    if os.path.exists(loc):
        python_dll = loc
        print(f"✓ Found Python DLL: {python_dll}")
        break

binaries = []
if python_dll:
    binaries.append((python_dll, '.'))

# SSL DLLs - robust detection for Python/_ssl and OpenSSL DLLs
print("\nSearching for SSL DLLs and _ssl module...")

import sysconfig
from importlib import util as _importutil

ssl_patterns = [
    'libssl-3.dll', 'libcrypto-3.dll',
    'libssl*.dll', 'libcrypto*.dll',
    'ssleay32.dll', 'libeay32.dll'
]

found_ssl_dlls = []

# Build a set of candidate search paths (common locations)
candidate_paths = set()
candidate_paths.update([
    python_path,
    python_exe_dir,
    os.path.join(python_path, 'DLLs'),
    os.path.join(python_exe_dir, 'DLLs'),
    os.path.join(python_path, 'Lib', 'site-packages'),
    os.path.join(python_path, 'Library', 'bin'),
    os.path.join(python_exe_dir, 'Library', 'bin'),
    os.path.join(sys.base_prefix, 'DLLs'),
    os.path.join(sys.base_prefix, 'Lib', 'site-packages'),
    os.path.join(sys.base_prefix, 'Library', 'bin'),
    'C:\\Windows\\System32',
    'C:\\Windows\\SysWOW64',
    'C:\\OpenSSL-Win64\\bin',
    'C:\\OpenSSL\\bin',
    'C:\\Program Files\\OpenSSL-Win64\\bin',
    'C:\\Program Files\\OpenSSL\\bin',
])

# Also include paths from sysconfig if available
try:
    paths = sysconfig.get_paths()
    for v in ('data', 'platlib', 'scripts'):
        p = paths.get(v)
        if p:
            candidate_paths.add(p)
except Exception:
    pass

# Search for DLL patterns in candidate paths
for search_path in list(candidate_paths):
    if not search_path or not os.path.exists(search_path):
        continue
    for pattern in ssl_patterns:
        for dll in glob.glob(os.path.join(search_path, pattern)):
            dll = os.path.abspath(dll)
            if dll not in found_ssl_dlls:
                found_ssl_dlls.append(dll)
                print(f"✓ Found SSL DLL: {dll}")

# Try to import _ssl to find its .pyd and directory
try:
    if _importutil.find_spec('_ssl'):
        import _ssl
        ssl_file = getattr(_ssl, '__file__', None)
        if ssl_file:
            ssl_file = os.path.abspath(ssl_file)
            if ssl_file not in [b[0] for b in binaries]:
                binaries.append((ssl_file, '.'))
                print(f"✓ Added _ssl module: {ssl_file}")

            ssl_dir = os.path.dirname(ssl_file)
            for pattern in ssl_patterns:
                for dll in glob.glob(os.path.join(ssl_dir, pattern)):
                    dll = os.path.abspath(dll)
                    if dll not in found_ssl_dlls:
                        found_ssl_dlls.append(dll)
                        print(f"✓ Found SSL DLL in _ssl dir: {dll}")
except Exception as e:
    print(f"Could not import _ssl or inspect it: {e}")

# Add discovered SSL DLLs to binaries (deduplicate)
for dll in found_ssl_dlls:
    if dll and dll not in [b[0] for b in binaries] and os.path.exists(dll):
        binaries.append((dll, '.'))

if not found_ssl_dlls and not any('_ssl' in os.path.basename(b[0]) for b in binaries):
    print("\n" + "!"*60)
    print("WARNING: NO SSL DLLs OR _ssl MODULE FOUND! HTTPS may not work at runtime.")
    print("!"*60)
    print("\nTo fix: install OpenSSL for Windows or ensure Python's _ssl is present and retry build.")
else:
    print(f"\n✓ Total SSL-related binaries found/added: {len([b for b in binaries if os.path.basename(b[0]).lower().startswith('lib') or '_ssl' in os.path.basename(b[0]).lower()])}")

# ------------------------------------------------------------------
# Ensure critical _ssl and OpenSSL DLLs are explicitly included
# This helps when PyInstaller's automatic detection misses files.
# ------------------------------------------------------------------
explicit_candidates = []

# Common locations to check for _ssl.pyd and OpenSSL DLLs
check_paths = [
    os.path.join(python_path, 'DLLs'),
    os.path.join(python_exe_dir, 'DLLs'),
    os.path.join(sys.base_prefix, 'DLLs'),
    os.path.join(python_path, 'Library', 'bin'),
    os.path.join(sys.base_prefix, 'Library', 'bin'),
    os.path.join(python_path, 'Lib', 'site-packages'),
    python_path,
    python_exe_dir,
    'C:\\Windows\\System32',
    'C:\\Windows\\SysWOW64',
]

ssl_names = ['_ssl.pyd', 'libssl-3.dll', 'libcrypto-3.dll', 'libssl*.dll', 'libcrypto*.dll', 'ssleay32.dll', 'libeay32.dll']

for base in check_paths:
    if not base or not os.path.exists(base):
        continue
    for name in ssl_names:
        for p in glob.glob(os.path.join(base, name)):
            p = os.path.abspath(p)
            if p not in [b[0] for b in binaries]:
                explicit_candidates.append(p)

# Also try to locate _ssl via import in the build env (again) and include siblings
try:
    import _ssl as _ssl_mod
    ssl_mod_file = getattr(_ssl_mod, '__file__', None)
    if ssl_mod_file:
        ssl_mod_file = os.path.abspath(ssl_mod_file)
        if ssl_mod_file not in [b[0] for b in binaries]:
            explicit_candidates.append(ssl_mod_file)
        ssl_mod_dir = os.path.dirname(ssl_mod_file)
        for pattern in ['libssl-3.dll', 'libcrypto-3.dll', 'libssl*.dll', 'libcrypto*.dll']:
            for p in glob.glob(os.path.join(ssl_mod_dir, pattern)):
                p = os.path.abspath(p)
                if p not in [b[0] for b in binaries]:
                    explicit_candidates.append(p)
except Exception:
    pass

# Add explicit candidates to binaries (unique)
for p in explicit_candidates:
    if os.path.exists(p) and p not in [b[0] for b in binaries]:
        binaries.append((p, '.'))
        print(f"✓ Explicitly added SSL-related file: {p}")

# --- Hardcode user's Python 3.13 DLL locations as a last resort ---
# These paths are common for a standard Python install on Windows x64.
py_install = r"C:\Program Files\Python313"
hard_paths = [
    os.path.join(py_install, 'DLLs', '_ssl.pyd'),
    os.path.join(py_install, 'DLLs', 'libssl-3.dll'),
    os.path.join(py_install, 'DLLs', 'libcrypto-3.dll'),
]
for hp in hard_paths:
    if os.path.exists(hp) and hp not in [b[0] for b in binaries]:
        binaries.append((hp, '.'))
        print(f"✓ Forced-include: {hp}")


print("="*60)
print(f"Total binaries to include: {len(binaries)}")
print("="*60 + "\n")

# Analysis
# Analysis
a = Analysis(
    ['Weather.py'],
    pathex=[],
    binaries=binaries,
    datas=[item for item in [
        ('updater\\updater.exe', 'updater') if os.path.exists('updater\\updater.exe') else None,
        ('Weather_icon.ico', '.') if os.path.exists('Weather_icon.ico') else None,
    ] if item is not None],
    hiddenimports=[
        # GUI
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        '_tkinter',

        # SSL / HTTPS (CRITICAL!)
        'ssl',
        '_ssl',
        'http',
        'http.client',
        'urllib',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        'urllib3',
        'certifi',

        # Requests
        'requests',
        'requests.adapters',
        'requests.packages',
        'requests.packages.urllib3',
    ],
    hookspath=[],
    hooksconfig={},
    excludes=[
        # Grote packages die niet nodig zijn
        'matplotlib', 'numpy', 'pandas', 'PIL', 'scipy',
        'IPython', 'jupyter', 'notebook',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx', 'kivy',
        'unittest', 'pytest', 'nose', 'pydoc', 'doctest',
        'pdb', 'bdb', 'cmd', 'code', 'codeop',
        'ftplib', 'smtplib', 'imaplib', 'poplib',
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Weather',
    version='version.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name='Weather',
)
