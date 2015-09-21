# -*- mode: python -*-
a = Analysis(['C:\\Dropbox\\CUSTOMER_ENGINEERING\\DroopCharTool_V1\\DroopCharSource\\droopCharTool.py'],
             pathex=['C:\\Dropbox\\CUSTOMER_ENGINEERING\\DroopCharTool_V1\\DroopCharSource'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='droopCharTool.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
