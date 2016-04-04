
__author__ = 'aliparsai'


import sys
import os

if len(sys.argv) < 3:
    print("""
    ReportParser by Ali Parsai

    Usage: {} [input] [output] [threshold]


    """.format(os.path.basename(sys.argv[0])))

    sys.exit(0)


inputFile = sys.argv[1]
outputFile = sys.argv[2]
thresholdRange = int(sys.argv[3])

if thresholdRange <= 0:
    thresholdRange = 1


if not os.path.isfile(inputFile):
    print("Error: input file does not exist.")
    sys.exit(1)

# inputLines = list()

with open(inputFile, 'r') as inputHandle:
        inputLines = inputHandle.readlines()



for threshold in range(0, thresholdRange+1):
    outputLines = list()

    
    for line in inputLines:
        className = line.split(":", 1)[0].replace(".java", "").replace("/", ".")
        survived = int(line.split("(")[1].split("/")[0])
        killed = int(line.split("(")[2].split("/")[0])
        total = survived + killed

        if total >= threshold:
            outputLines.append([className, str(survived), str(killed), str(total)])

    i = 0
    
    tmp = outputFile.rsplit('.', 1)
    outputCurrentFile = tmp[0] + "-" + str(threshold) + "." + tmp[1]

    with open(outputCurrentFile, 'a') as outputHandle:
        for line in outputLines:
            i += 1
            outputHandle.write(",".join(line))
            outputHandle.write(os.linesep)
            sys.stdout.write(str(i) + " lines wrote.\r")

        sys.stdout.write(os.linesep)



