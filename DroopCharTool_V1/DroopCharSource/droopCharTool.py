#!/usr/bin/env python3
""" Retrieve and print words from a URL
Usage:
	python.exe droopCharTool.py rootDirectory deviceType
"""

import xml.etree.ElementTree as ET	# For XML Library
import xlsxwriter					# For Excel Library
import os							# for operating system file management
from collections import defaultdict # supports auto-vivification for dictionaries
import sys							# used for getting command-line arguments

#---------- INPUT: Root Directory from which to process the data -----------#
# with a batch script, these argument are updated via the command line
rootDir    = 'C:/Users/mihughes/Desktop/Droop_CHAR/Sweep_Data'	# make sure not to have a trailing '\'
type       = 'MTP' # string which forms part of each worksheet name
nvFileName = 'testQCN.Xml'

#---------- INPUT: XML Parsing Inputs ----------#
testName	  = "Test"
testAttribTag = "I"
testIDTag     = "6020200"
testIDName    = "LTE_MaxPower"
chanTag		  = "Channel"
rbTag         = "UL_Start_RB"
maxPwrTag     = "MaxTxPwr"

#---------- INPUT: Excel Naming Convention Inputs ---------#
workbookName = 'DroopCharData'
workbookType = 'xlsx'

#---------- INPUT: Worksheet "Column A" Arguments ---------#
fixedHeadingList = [ 'FBRx Measurement Mode',
					 'Measurement Equalizer (real)',
					 'Measurement Equalizer (imag)',
					 'Averaging Method',
					 'New equalizer length',
					 'Magnitude ripple tolerance',
					 'Magnitude ripple target',
					 'Magnitude ripple limit',
					 'Measurement Freqs'
					]
variableHeadingRoot = 'Data'

#---------- INPUT: Measurement Equalizer Values - BW dependent ---------#
# static NV values -- note, these are updated by reading the QCN
real_bw10 = [-145,-755,17594,1128,-2663,1938,-943,231]
imag_bw10 = [   0,   0,    0,   0,    0,   0,   0,  0]
real_bw20 = [-1373,18383,1058,-3232,2589,-1471,533,-103]
imag_bw20 = [    0,    0,   0,    0,   0,    0,  0,   0]
# variables for holding the calibrated NV items
bandSpec_real_bw10 = []
bandSpec_real_bw20 = []
bandSpec_imag_bw10 = []
bandSpec_imag_bw20 = []

#---------- INPUT: Measurement Equalizer Values - BW dependent ---------#
#staticDroopNVID_BW_Dict = []
#staticDroopNVID_BW_Dict['10'] = '27476'
#staticDroopNVID_BW_Dict['20'] = '27478'



#---------- INPUT: Worksheet "Column B" Arguments ---------#
# 'NA' indicates that this value is variable and will be updated during processing
colBArguments = [ -1,	 # FBRx mode for BW (will be updated)
				  -1,	 # 1st real coefficient of the measurement equalizer (will be updated)
				  0,	 # 1st real coefficient of the measurement equalizer (will be updated)
				  1,	 # averaging method
				  10,	 # new equalizer length
				  0.025, # Magnitude Ripple Tolerance
				  0.05,  # Magnitude Ripple Target
				  0.2,	 # Magnitude Ripple Limit
				  -1	 # 1st element of Measurement Freqs (will be updated)
				 ]

fbrxMode_bw10 = 3		# FBRx mode for BW = 10 MHz
fbrxMode_bw20 = 1		# FBRx mode for BW = 20 MHz

#---------- INPUT: Variable Arguments ---------#
maxRB_bw10 = 50
maxRB_bw20 = 100
	
		
############## Helper FUNCTIONS ################
def RemoveDupFromList(inputList):
	uniqueList = []
	for item in inputList:
		if item not in uniqueList:
			uniqueList.append(item)
	return uniqueList
# END def RemoveDupFromList(inputList):

def ComputeMeasFreqFromRb(inputRb, bw):
	bwRB = maxRB_bw20
	if (int(bw) == 10):
		bwRB = maxRB_bw10
	return ( (float(rb) - bwRB/2)*0.18 + 0.09 )
# END def ComputeMeasFreqFromRb(inputRb, bw):
	
def FillColumnB_VariableArguments(bw, realList, imagList):
	colBArguments[0] = 0
	
	if (bw == 10):
		colBArguments[0] = fbrxMode_bw10
	elif (bw == 20):
		colBArguments[0] = fbrxMode_bw20
	else:
		print('Error: Incorrect BW read. Only accept 10 and 20')	
	colBArguments[1] = realList[0]
	colBArguments[2] = imagList[0]
# END def FillColumnB_VariableArguments(bw):		

def usage():
	print("Usage: %s <rootDirectory> <deviceType> <nvFileName.", sys.argv[0])
	exit(1)
# END def usage():
	
def Extract_Droop_Static_NV():
	## Read in the NV file
	nvFile = rootDir + '/' + nvFileName
	nvTree = ET.parse( nvFile )		
		
	## Fill the static NVs
	root = nvTree.getroot()
	bw10_staticNV = []
	bw20_staticNV = []
	for child in root:
		curNvID =  child.attrib.get('id', None)
		if ( curNvID == '27476'):	
			bw10_staticNV = child.text
		elif ( curNvID == '27478'):
			bw20_staticNV = child.text			
		if (bw10_staticNV and bw20_staticNV):
			break

	# split the string input based upon ','
	bw10_static_List = bw10_staticNV.split(',')
	bw20_static_List = bw20_staticNV.split(',')				
	
	# fill the NV structs
	global real_bw10
	global imag_bw10
	global real_bw20
	global imag_bw20
	real_bw10 = []
	imag_bw10 = []
	real_bw20 = []
	imag_bw20 = []
	numElemIndex = 2
	numCoef = int(bw10_static_List[numElemIndex])
	for realVal in bw10_static_List[numElemIndex+1:numElemIndex+1+numCoef]:
		real_bw10.append(int(realVal))
		imag_bw10.append('0')
	numCoef = int(bw20_static_List[numElemIndex])
	for realVal in bw20_static_List[numElemIndex+1:numElemIndex+1+numCoef]:
		real_bw20.append(int(realVal))
		imag_bw20.append('0')	
# END def Extract_Droop_Static_NV():		
		
def Extract_Calibrated_NV( bw, band ):
	nameTag = 'RFNV_LTE_C0_' + band + '_FBRX_DROOP_FIR_FILTER_COEFF_Z_I'
	
	# hex values of interest in the QCN
	dataType = '007b'
	bw10 = '000a'
	bw20 = '0014'
	
	## Read in the NV file
	nvFile = rootDir + '/' + nvFileName
	nvTree = ET.parse( nvFile )		
		
	## Fill the calibrated NVs
	root = nvTree.getroot()
	nvString = ''  # this will include all bandwidths, so BW10 and BW20 must be extracted
	
	for child in root:
		curNvName =  child.attrib.get('name', None)
		if (curNvName == nameTag):
			nvString = child.text
			break
	
	# remove all spaces
	nvList  = nvString.split(' ')
	nvList2 = []
	#print(nvList)
	
	numElem = len(nvList)
	# convert to hex
	i = 0
	while (i < numElem-1):
		nvList2.append( nvList[i+1] + nvList[i] )
		i += 2
		
	bw10Filter = []
	bw20Filter = []
	
	# combine the 4 byte values
	nvList3 = []
	numElem = len(nvList2)
	i = 0
	while (i < numElem-1):
		if ( nvList2[i] == dataType ):
			i += 1
			curBW = nvList2[i]
			if (curBW == bw10 or curBW == bw20):
				i += 1
				subStr = nvList2[i]
				numCoef = int(subStr[:2],16)
				i += 1
				max = i + 2*numCoef - 1
				while (i < max):
					hexVal = nvList2[i+1] + nvList2[i]
					hexVal = int(hexVal,16)
					if (0x80000000 & hexVal):
						hexVal = ((0xFFFFFFFF ^ hexVal) + 1) * -1
					i += 2
					if (curBW == bw10):
						bw10Filter.append( hexVal )
					else:
						bw20Filter.append( hexVal )
			else:
				i += 1
		else:
			i += 1	
	
	global bandSpec_real_bw10
	global bandSpec_real_bw20
	global bandSpec_imag_bw10
	global bandSpec_imag_bw20	

	# returning if bw == 10
	if (int(bw) == 10):
		if (not bw10Filter):
			return 0
		else:
			bandSpec_real_bw10 = []
			bandSpec_imag_bw10 = []
			for val in bw10Filter:
				bandSpec_real_bw10.append(val)
				bandSpec_imag_bw10.append(0)
			return 1
			
		# returning if bw == 20
	if (int(bw) == 20):
		if (not bw20Filter):
			return 0
		else:
			bandSpec_real_bw20 = []
			bandSpec_imag_bw20 = []
			for val in bw20Filter:
				bandSpec_real_bw20.append(val)
				bandSpec_imag_bw20.append(0)
			return 1		
# END def Extract_Calibrated_NV( bw, band ):		

	
################# MAIN EXECUTION ################# 
if __name__ == '__main__':

	#argList = str(sys.argv)
	#print('argList',argList)
	rootDir     = sys.argv[1]
	type        = sys.argv[2]
	nvFileName  = sys.argv[3]

	print('\n')
	print('#-------------- Start Droop Char Data Extraction --------------#')
	print('#------ From Directory:', rootDir)
	print('#------ For Type:      ', type)
	print('#------ For NV File:   ', nvFileName)
	print('\n')
	
	print('----- Read', len(sys.argv), 'input arguments.' )
	print('----- Arguments are: ', str(sys.argv) )  
	print('\n')
	
	if ( len(sys.argv) != 4 ):
		usage()
		sys.exit( "\nException: Too few arguments were entered! Please be sure to have the 'rootDirectory' and 'deviceType' included")
		
	#---------- Output: Data Structures ---------#
	Master_Dict   = lambda: defaultdict(Master_Dict)	# make an anonymous function for auto-vivification
	outputDict    = Master_Dict()						# auto-vivify the outputDict
	bandList      = []

	#--------- Step 0: Iterate over the sub-directories ---------#
	subDirList = os.listdir(rootDir)
	if not subDirList:
		sys.exit('Error: no sub-directories found. This function assumes the following structure: rootDir->testDir->bandDir')
	
	# START cuDir Loop
	for curDir in subDirList:		
		# Get the sub-directories below rootDir		
		subDir1 = rootDir + '/' + curDir
		# skip if the path is a file
		if ( os.path.isfile(subDir1) ):
			continue
		os.chdir(subDir1)
		
		#--------- Step 1: Iterate over the available bands and BWs --------#
		subDirList1 = os.listdir(subDir1)
		
		# START curSubDir Loop (BAND LOOP)
		for curSubDir in subDirList1:	
			# determine the current band from the curSubDir name
			start = 0;
			end   = curSubDir.find('_')
			curBand = curSubDir[start:end]
			subDir2 = subDir1 + '/' + curSubDir
			os.chdir(subDir2)		
			
			bandList.append(curBand)
			
			#--------- Step 2: Iterate over each file for the current BW and Band --------#
			curFileList = os.listdir(subDir2)
			
			# START curFile Loop (FILE LOOP)
			for curFile in curFileList:
			
				# extract the bandwidth
				start = curFile.find('_') + 1
				end   = curFile.find('MHz') 
				curBW = curFile[start:end]
				# skip the file if it isn't for the desired bandwidths
				if (curBW != '10' and curBW != '20'):
					#print('----- !Skipping bw = ', curBW)
					continue
				
				print('----- Current SubDir:', curDir)
				print('----- Current Band:  ', curBand)
				print('----- Current BW:    ', curBW)								
				print('-- Processing File:  ', curFile)
				print('\n')					

				#--------- Step 3: Process the Current File --------#
				tree = ET.parse(curFile)
				# set the root of the XML file
				root = tree.getroot()
				
				#iterate over the children
				# START childNode Loop
				for child in root:
					#-------- find the 'Test' nodes
					# START testNode Loop
					for test in root.iter(testName):
						#------ check if the attribute matches what we want
						if (test.attrib.get(testAttribTag, None) == testIDTag):
							# begin extracting the desired information
							name = test.find('Name')
							# make sure the XML file is formatted as expected
							if (name.text != testIDName):
								print("Error: XML not formatted properly.")
							#------ Find the desired sections of the DataSetCollection
							DSC     = test.find('DataSetCollection')
							dataSet = DSC.find('DataSet')
							#------ Get the Inputs: Channel and UL_Start_RB
							inputs  = dataSet.find('Inputs')
							for DI in inputs.findall('DI'):
								curDI = DI.find('N')
								if (curDI.text == chanTag):
									chanNum = DI.find('V')
									curChannel = chanNum.text	#output dictionary key
								elif (curDI.text == rbTag):
									rbNum = DI.find('V')
									curStartRB = rbNum.text		#output dictionary key
							#------ Get the Output: Max Power
							outputs = dataSet.find('Outputs')
							for results in outputs.iter('Result'):
								DI    = results.find('DI')
								curDI = DI.find('N')
								if (curDI.text == maxPwrTag):
									mxPwr = DI.find('V')
									curMaxPower = mxPwr.text
									break;	# data is found, so break out of the loop
									
							#------ Add data to the dictionary						
							outputDict[curBand][curBW][curChannel][curDir][int(curStartRB)] = float(curMaxPower)
				
					# END testNode Loop (CHANNELs and DATA)						
				# END childNode Loop (CHANNELs and DATA)					
			# End curSubDir Loop
	# END curDir Loop			
	
	#----------- Step 4: re-process the result iterators ---------#
	uniqueBands = RemoveDupFromList(bandList)
			
	#----------- Step 5: now, write the data from this current file to Excel ---------#
	# Output Data Container --> dictionary[Band][BW][Channel][channel_iter][RB][MaxPower]
	fullWorkbookName = rootDir + '/' + workbookName + '_' + type + '.' + workbookType
	workbook = xlsxwriter.Workbook( fullWorkbookName )	
	print('\n')
	print('----- Writing Data to Excel -----')

	# Get the droop coefficient static NVs
	# the BW10 and BW20 static NVs are filled by this function
	Extract_Droop_Static_NV()
	
	## Iterate over Band
	for band in uniqueBands:
		## Iterate over BW
		for bw in outputDict[band]:
		
			## Find the appropriate droop coefficient NV to use for this band/BW combination.
			#--------- Step 3: Process the Current File --------#
			# set the root of the XML file
			#root = nvTree.getroot()
			#iterate over the children
			#for child in root:	
			b_foundCalNV = Extract_Calibrated_NV( bw, band )			
			# Determine which droop-filter coefficient list to use
			if (b_foundCalNV):
				if (int(bw) == 10):
					coefListReal = bandSpec_real_bw10
					coefListImag = bandSpec_imag_bw10
				else:
					coefListReal = bandSpec_real_bw20
					coefListImag = bandSpec_imag_bw20
			else:
				if (int(bw) == 10):
					coefListReal = real_bw10
					coefListImag = imag_bw10
				else:
					coefListReal = real_bw20
					coefListImag = imag_bw20		

			worksheetName = type + '_' + band + '_' + bw
			worksheet     = workbook.add_worksheet(worksheetName)	
			worksheet.set_column('A:A',30)		
			FillColumnB_VariableArguments( int(bw), coefListReal, coefListImag )					
	
			rowIdx = 0
			colIdx = 0
			# fill column A				
			for heading in fixedHeadingList:
				worksheet.write_string(rowIdx,colIdx,heading)
				rowIdx += 1
			# fill column B
			rowIdx = 0
			colIdx = 1
			# update the equalizer length - no, needs to be hardcoded to 10
			#colBArguments[4] = len(coefListReal)
			for curVal in colBArguments:
				worksheet.write_number( rowIdx,colIdx,float(curVal) )
				rowIdx += 1
			# fill the equalizer coefficients - real
			rowIdx = 1
			colIdx = 2
			for curVal in coefListReal[1:]:
				worksheet.write_number( rowIdx,colIdx,float(curVal) )
				worksheet.write_number( rowIdx+1,colIdx,float(coefListImag[colIdx-2]) )
				colIdx += 1	
								
			# Fill in the max power results
			rowIdx     = 9	# the start of data writing
			rowIdxFreq = 8
			alreadyFilledFreq = 0;
			for chan in outputDict[band][bw]:
				for chanIter in outputDict[band][bw][chan]:	
					print('- ',end="")
					colIdx = 0
					worksheet.write_string(rowIdx,colIdx, 'Data_' + chan + '_' + chanIter )
					colIdx = 1
					#obtain the current rb list for the current band and bw and chan and chanIter
					curRbList = []
					for tempRB in outputDict[band][bw][chan][chanIter]:
						curRbList.append(tempRB)
					curRbList.sort()
					for rb in curRbList:						
						worksheet.write_number( rowIdx,colIdx, float(outputDict[band][bw][chan][chanIter][rb]) )
						if (alreadyFilledFreq == 0):
							worksheet.write_number( rowIdxFreq,colIdx, float(ComputeMeasFreqFromRb(rb, bw)) )
						colIdx += 1
					rowIdx += 1
					alreadyFilledFreq = 1;

	# close the workbook, once all bands have been iterated over	
	workbook.close()
	print('\nSaved output to: ', fullWorkbookName)
	print('\n-------- FINISHED --------')
	
	
	