# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

binaries = []
try:
    from pyftdi.ftdi import Ftdi

    Ftdi.list_devices()
    binaries.append(('C:\\Windows\\System32\\libusb0.dll', '.'))

except ValueError as err:
    if 'No backend available' in str(err):
        # This occurs if libusb is not installed.
        # Refer https://eblot.github.io/pyftdi/troubleshooting.html
        pass
    else:
        raise

a = Analysis(['qtoscillo.py'],
             pathex=['.'],
             binaries=binaries,
             datas=[],
             hiddenimports=['usb', 'pyftdi.serialext.protocol_ftdi'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts, [],
    exclude_binaries=True,
    name='qtoscillo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='qtoscillo')
