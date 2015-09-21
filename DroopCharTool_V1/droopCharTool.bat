@echo off

SET rootDirectory="\\qct-lab-39\Dropbox\CUSTOMER_ENGINEERING\DroopCharTool_V1\Sweep_Data"
SET deviceType="MTP" 
SET nvFileName="testQCN.Xml"

REM %rootDirectory% = the root path of the files to be processed
REM %deviceType%    = the device type that was characterized; for example, MTP. 
REM %nvFileName%    = the XML version of the QCN file to be used
\\qct-lab-39\Dropbox\CUSTOMER_ENGINEERING\DroopCharTool_V1\DroopCharSource\dist\droopCharTool.exe %rootDirectory% %deviceType% %nvFileName%

pause