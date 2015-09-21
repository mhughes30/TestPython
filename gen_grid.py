#!/usr/bin/env python3

import sys
import random
import statistics 

input2 = []

lowest = 0
highest = 0
count2 = 0
sum2 = 0;
mean2 = 0;

while(1):
	msg = "enter a number or enter to finish:"
	curIn = input(msg)
	
	if curIn:
		try:
			number = int(curIn)
			
		except ValueError as error:
			print(err)
			continue
		input2.append(number)
	else:
		break
			
sum2  = sum(input2)
mean2 = sum2 / float(len(input2))
count2 = len(input2)
lowest = min(input2)
highest = max(input2)
	
print("numbers:", input2);
print("count:",count2);
print("mean:",mean2);
print("lowest:",lowest);
print("highest:",highest);
	
	
	
	