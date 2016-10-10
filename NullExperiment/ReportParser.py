
__author__ = 'aliparsai'


import sys
import os

if len(sys.argv) < 3:
    print("""
    ReportParser by Ali Parsai

    Usage: {} [input] [output]


    """.format(os.path.basename(sys.argv[0])))

    sys.exit(0)


inputFile = sys.argv[1]
outputFile = sys.argv[2]

if not os.path.isfile(inputFile):
    print("Error: input file does not exist.")
    sys.exit(1)

# inputLines = list()

with open(inputFile, 'r') as inputHandle:
        inputLines = inputHandle.readlines()

outputLines = list()

for line in inputLines:
    className = line.split(":", 1)[0].replace(".java", "").replace("/", ".")
    survived = int(line.split("(")[1].split("/")[0])
    killed = int(line.split("(")[2].split("/")[0])
    total = survived + killed
    coverage = ((killed * 1000) / total) / 10.0

    outputLines.append([className, str(killed), str(survived), str(total), str(coverage)])

i = 0

with open(outputFile, 'a') as outputHandle:
    outputHandle.write("Class Name,Killed Mutants,Survived Mutants,Total,Coverage")
    for line in outputLines:
        i += 1
        outputHandle.write(",".join(line))
        outputHandle.write(os.linesep)
        sys.stdout.write(str(i) + " lines wrote.\r")


sys.stdout.write(os.linesep)



