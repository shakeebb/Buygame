# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['buygame.py'],
             pathex=['venv/Lib/site-packages', 'gui', 'gui/login', 'gui/survey', 'gui/gui_common', 'common'],
             binaries=[],
             datas=[('gui/tiles', 'gui/tiles')],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='pyi-buygame-mac',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
app = BUNDLE(exe,
             name='pyi-buygame-mac.app',
             icon=None,
             bundle_identifier=None,
             info_plist={
                         'NSPrincipalClass': 'NSApplication',
                         'NSAppleScriptEnabled': False,
                         'CFBundleDocumentTypes': [
                             {
                                 'CFBundleTypeName': 'My File Format',
                                 'CFBundleTypeIconFile': 'MyFileIcon.icns',
                                 'LSItemContentTypes': ['com.example.myformat'],
                                 'LSHandlerRank': 'Owner'
                                 }
                             ]
                         },
	    )
