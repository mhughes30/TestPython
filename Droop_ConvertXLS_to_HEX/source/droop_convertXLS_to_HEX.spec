# -*- mode: python -*-
a = Analysis(['C:\\Dropbox\\CUSTOMER_ENGINEERING\\Droop_ConvertXLS_to_HEX\\source\\droop_convertXLS_to_HEX.py'],
             pathex=['C:\\Dropbox\\CUSTOMER_ENGINEERING\\Droop_ConvertXLS_to_HEX\\source'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='droop_convertXLS_to_HEX.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
