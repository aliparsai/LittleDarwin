import sys


for filename in sys.argv[1:]:
	fileHandle = open(filename, "r")
	lines = fileHandle.readlines()
	
	Expected = 0 
	HSFK = 0
	HKFS = 0
	for line in lines:
		stuff = line.split(",")
		Expected += int(stuff[1])
		HSFK += int(stuff[2])
		HKFS += int(stuff[3])
	
	
	total = Expected + HSFK + HKFS
	print  "&", Expected, "(" +str(round(Expected*100/float(total),2)) + "\%) & ", HKFS, "&", HSFK, " &", total 
		
