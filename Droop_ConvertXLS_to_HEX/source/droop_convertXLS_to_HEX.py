#!/usr/bin/env python3
""" Retrieve and print words from a URL
Usage:
	python.exe droopCharTool.py rootDirectory deviceType
"""

import xlrd  # for reading in Excel files
import re    # for regular expressions usage

import xml.etree.ElementTree as ET	# For XML Library
import os							# for operating system file management
from collections import defaultdict # supports auto-vivification for dictionaries
import sys							# used for getting command-line arguments

#---------- INPUT: Root Directory from which to process the data -----------#
# with a batch script, these argument are updated via the command line
rootDir    = 'C:/Dropbox/CUSTOMER_ENGINEERING/Droop_ConvertXLS_to_HEX'	# make sure not to have a trailing '\'
fileName = 'FBRxEqualizers.xlsx'

#---------- INPUT: Excel Naming Convention Inputs ---------#
outputFileName = '_DroopNVs'
outputType     = '.xml'
# some global variables
nvSearchTerm  = 'NV'
dataType      = '7b 00'	 # The FBRX_LTE_bw_Droop_cal_Type ID (123 in Hex Little Endian format)
version       = '00 00'  # the version number, which is the 1st value in the NV
groupDelayIdx = 2
numFiltTapIdx = 3
dataStartIdx  = numFiltTapIdx + 1
dataEndIdx    = dataStartIdx + 1 # will be updated later

#---------- INPUT: Dictionary of Band to NV ID ---------#
bandToNvIdDict = {  'B1'    : '"28493"',
					'B2'    : '"28494"',
					'B3'    : '"28495"',
					'B4'    : '"28496"',
					'B5'    : '"28497"',
					'B6'    : '"28498"',
					'B7'    : '"28499"',
					'B8'    : '"28500"',
					'B9'    : '"28501"',
					'B10'   : '"28502"',
					'B11'   : '"28503"',
					'B12'   : '"28504"',
					'B13'   : '"28505"',
					'B14'   : '"28506"',
					'B17'   : '"28507"',
					'B18'   : '"28508"',
					'B19'   : '"28509"',
					'B20'   : '"28510"',
					'B21'   : '"28511"',
					'B23'   : '"28512"',		
					'B25'   : '"28513"',
					'B26'   : '"28514"',
					'B28'   : '"28516"',
					'B28_B' : '"28517"',
					'B29'   : '"28518"',
					'B30'   : '"28519"',
					'B31'   : '"28520"',
					'B34'   : '"28521"',					
					'B38'   : '"28522"',
					'B39'   : '"28523"',
					'B39_B' : '"28524"',
					'B40'   : '"28525"',
					'B40_B' : '"28526"',
					'B41'   : '"28527"',
					'B41_B' : '"28528"',
					'B41_C' : '"28529"',	
					'B42'   : '"28530"',	
					'B43'   : '"28531"',	
					'B44'   : '"28532"'						
				}


#---------- INPUT: Measurement Equalizer Values - BW dependent ---------#


#---------- INPUT: Worksheet "Column B" Arguments ---------#

		
############## Helper FUNCTIONS ################
def CreateXMLNvOutput( band, dataString ):
	
	id             = bandToNvIdDict[band]
	subscriptionID = '"0"'
	name           = '"RFNV_LTE_C0_' + band + '_FBRX_DROOP_FIR_FILTER_COEFF_Z_I"'
	mapping        = '"byteStream"'
	encoding       = '"hex"'
	index          = '"0"'
	
	nvString = '<NvItem id=' + id + ' subscriptionid=' + subscriptionID + ' name=' + name + ' mapping=' + mapping + ' encoding=' + \
				encoding + ' index=' + index + '>' + dataString + '</NvItem>'
				
	return nvString	
	
def AddUnderscoreToSplitBand( band ):
	
	lastChar = band[-1:]
	
	if not lastChar.isdigit():
		if ( lastChar.upper() != 'A' ):
			outputBand = band[:-1] + '_' + lastChar
		else:
			outputBand = band[:-1]
	else:
		return band
		
	# make sure it is converted to upper case
	outputBand = outputBand.upper()
	
	return outputBand


def ConvertUint16_to_Hex( uint16Val ):
	intVal = int(uint16Val)
	
	byte0 = intVal & 0x00FF
	byte0 = format(byte0,'02x')
	byte1 = intVal & 0xFF00
	byte1 = format(byte1,'02x')	
	
	#combine the bytes into Little Endian format
	outputString = byte0[:2] + ' ' + byte1[:2] + ' '

	return outputString

def MakeSureByteIsCorrect( inputByte ):
	
	byte = inputByte

	if (len(inputByte) == 1):
		byte = '0' + inputByte
	elif (len(inputByte) == 0):
		byte = '00'	
		
	return byte

def CreateHexFormattedDataTable( inputList, groupDelay, numFiltTaps, bw  ):
	# the output result
	outputString    = ''
	filtCoeffString = ''

	numBytes      = 4 * numFiltTaps # each element is an int32
	numBytesToPad = 128 - numBytes
		
	for val in inputList:
		intVal = int(val)
		# 2's compliment processing
		if (intVal < 0):
			intVal = ((0xFFFFFFFF ^ intVal) + 1) * -1
		# change the hexadecimal value to Little Endian format			
		byte0 = (intVal & 0x000000FF)
		byte0 = format(byte0,'02x')
		byte0 = MakeSureByteIsCorrect( byte0 )
		byte1 = (intVal & 0x0000FF00)
		byte1 = format(byte1,'02x')
		byte1 = byte1[:-2]
		byte1 = MakeSureByteIsCorrect( byte1 )
		byte2 = (intVal & 0x00FF0000)
		byte2 = format(byte2,'02x')
		byte2 = byte2[:-4]
		byte2 = MakeSureByteIsCorrect( byte2 )
		byte3 = (intVal & 0xFF000000)
		byte3 = format(byte3,'02x')
		byte3 = byte3[:-6]
		byte3 = MakeSureByteIsCorrect( byte3 )
		# combine the bytes into the Little Endian format
		littleEnd = byte0[:2] + ' ' + byte1[:2] + ' ' + byte2[:2] + ' ' + byte3[:2] + ' '
		
		filtCoeffString += littleEnd
		
	# pad zero's onto the end, if necessary, since each data table is 128 bytes longs
	byteIdx = 0
	while (byteIdx < numBytesToPad):
		filtCoeffString += '00 '
		byteIdx += 1
	
	hexGroupDelay = format(int(groupDelay),'02x')
	hexNumFiltTap = format(int(numFiltTaps), '02x')
	hexBW         = format(int(bw), '02x')
	outputString  = dataType + ' ' + hexBW + ' 00 ' + hexGroupDelay + ' ' + hexNumFiltTap + ' ' + filtCoeffString
	
	# return the string containing the properly formatted results
	return outputString

	
################# MAIN EXECUTION ################# 
if __name__ == '__main__':

	rootDir     = sys.argv[1]
	fileName    = sys.argv[2]

	filePath = rootDir + '/' + fileName
		
	print('\n')
	print('#-------------- Start FBRxEqualizers conversion --------------#')
	print('#------ Input File: ', filePath)
	print('#------ Output Path:', rootDir)
	print('\n')

	workbook = xlrd.open_workbook( filePath )
	
	Master_Dict    = lambda: defaultdict(Master_Dict)	# make an anonymous function for auto-vivification
	# dictionaries of Type -> Tech -> Band -> BW -> Data
	vectorDict     = Master_Dict()						# auto-vivify
	groupDelayDict = Master_Dict()
	numFiltTapDict = Master_Dict()
	
	##### Extract all of the data out of the worksheets, and place them in Containers #####
	for curWrksht in workbook.sheet_names():
		# check if the worksheet is one that we want
		if (curWrksht[0] == 'B'):
			tempBand = curWrksht
			# add an underscore to the band if necessary
			curBand = AddUnderscoreToSplitBand( tempBand )			
			print('Processing band: ', curBand)
			worksheet = workbook.sheet_by_name(curWrksht)
			# read the 1st column
			entireCol = worksheet.col(0)
			colSize = len(entireCol)
			# Find the location of the NV values
			nvRowIdx = 0;			
			for cellVal in entireCol:	# cellVal is a cell object
				# Find the location of "NV"
				if (cellVal.value == nvSearchTerm):
					desiredRowIdx = nvRowIdx	# initialize
					while (1):
						desiredRowIdx = nvRowIdx + 1
						# break out if the data size of the XLS column is exceeded
						if (desiredRowIdx >= colSize):
							break
						entireRow     = worksheet.row(desiredRowIdx)							
						tech_BW_Type  = entireRow[0].value.split()
						# skip to the next row if this row contains no band information
						if (tech_BW_Type == []):
							nvRowIdx += 1
							continue
						tech_BW       = tech_BW_Type[0].split('-')
						# identify the current technology and BW
						curTech = tech_BW[0]
						curBW   = tech_BW[1]
						# identify the device type
						curType = tech_BW_Type[1]
						curType = re.sub('[( )]', '', curType)
						# Extract the Group Delay and Number of Filter Coefficients parameters
						groupDelayDict[curType][curTech][curBand][curBW] = entireRow[groupDelayIdx].value
						numFiltTapDict[curType][curTech][curBand][curBW] = entireRow[numFiltTapIdx].value
						# Extract the Filter Coefficients
						vecIdx = 0
						filtList = []
						while vecIdx < numFiltTapDict[curType][curTech][curBand][curBW]:
							filtCoef = entireRow[dataStartIdx + vecIdx].value
							filtList.append( filtCoef )
							vecIdx += 1
						vectorDict[curType][curTech][curBand][curBW] = filtList
						
						# increment the row index
						nvRowIdx += 1
					
				# increase the NV row index	
				nvRowIdx += 1
	
	##### Convert all of the Filter Coefficient Data to a Hex-String And Write the Complete NV to an XMl File #####
	# All of the output result dictionaries contain the same keys	
	outputNvDataStringDict = Master_Dict()
	
	for type in groupDelayDict:
		#print('Type: ', type)
		curFileName = rootDir + '/' + type + outputFileName + outputType
		print('---- Writing File:', curFileName)
		FILE = open(curFileName, 'w')
		# write the opening XML tag
		FILE.write('<NvSource>' + '\n')
		for tech in groupDelayDict[type]:
			for band in groupDelayDict[type][tech]:
				numNvElements = len(groupDelayDict[type][tech][band])
				numElemHex    = ConvertUint16_to_Hex( numNvElements )
				# Begin creating the Hex Little Endian NV String
				outputNvDataStringDict[type][tech][band] = version + ' ' + numElemHex
				
				for bw in groupDelayDict[type][tech][band]:
					curNumFilterTaps = numFiltTapDict[type][tech][band][bw]
					curGroupDelay    = groupDelayDict[type][tech][band][bw]
					nvDataTableStr   = CreateHexFormattedDataTable( vectorDict[type][tech][band][bw], curGroupDelay, curNumFilterTaps, bw )
					# Add on the NV Data Tables
					outputNvDataStringDict[type][tech][band] = outputNvDataStringDict[type][tech][band] + nvDataTableStr
				
				#print(outputNvDataStringDict[type][tech][band])
				# produce the final XML output
				fullNvString = CreateXMLNvOutput( band, outputNvDataStringDict[type][tech][band] )
				# write the NV to the XML output file
				FILE.write(fullNvString + '\n')
		
		# close out the opening XML Tag
		FILE.write('</NvSource>')
		# Close the file
		FILE.closed
					
	
	
	print('\n-------- FINISHED --------')
	
	
	
	
	
	
	
	
	
	
	
	