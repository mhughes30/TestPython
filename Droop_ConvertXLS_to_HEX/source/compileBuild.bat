@echo off

SET pyInstaller="C:\Users\mihughes\Desktop\Python\pyinstaller-python3\pyinstaller.py"
SET specOption="--onefile
SET pyFile="droop_convertXLS_to_HEX.py" 
SET pySpec="droop_convertXLS_to_HEX.spec"

REM %rootDirectory% = the root path of the files to be processed
REM %deviceType%    = the device type that was characterized; for example, MTP. 
python.exe %pyinstaller% %specOption% %pyfile%

python.exe %pyinstaller% %pySpec%

pause