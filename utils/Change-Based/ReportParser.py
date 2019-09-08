
__author__ = 'aliparsai'


import sys
import os

def parse_report(input_lines):
    result = dict()
    for line in input_lines:
        className = line.split(":", 1)[0].replace(".java", "").replace("/", ".")
        survived = int(line.split("(")[1].split("/")[0])
        killed = int(line.split("(")[2].split("/")[0])

        result[className]=([survived, killed])
    return result


def open_report(file_path):
    if not os.path.isfile(file_path):
        print("Error: input file does not exist.")
        sys.exit(1)

    with open(file_path, 'r') as handle:
        result = handle.readlines()
    return result




if len(sys.argv) < 4:
    print("""
    ReportParser by Ali Parsai

    Usage: {} [input_base] [input_final] [output]


    """.format(os.path.basename(sys.argv[0])))

    sys.exit(0)


inputFileBase = sys.argv[1]
inputFileFinal = sys.argv[2]
outputFile = sys.argv[3]


inputLinesBase = open_report(inputFileBase)
inputLinesFinal = open_report(inputFileFinal)

outputLines = list()

baseResult = parse_report(inputLinesBase)
finalResult = parse_report(inputLinesFinal)

classNames = list()
classNames.extend(baseResult.keys())
classNames.extend(finalResult.keys())
classNamesUnique = set(classNames)

for className in classNamesUnique:
    if className not in baseResult.keys():
        outputLines.append(str(className)+",NA,NA,"+",".join([str(x) for x in finalResult[className]]))
        continue

    if className not in finalResult.keys():
        outputLines.append(str(className)+","+",".join([str(x) for x in baseResult[className]])+",NA,NA")
        continue

    if baseResult[className][0] != finalResult[className][0] or baseResult[className][1] != finalResult[className][1]:
        outputLines.append(str(className)+","+",".join([str(x) for x in baseResult[className]])+","+",".join([str(x) for x in finalResult[className]]))

with open(outputFile, 'a') as outputHandle:
    i = 0
    for line in outputLines:
        i += 1
        outputHandle.write(line)
        outputHandle.write(os.linesep)
        sys.stdout.write(str(i) + " lines wrote.\r")

    sys.stdout.write(os.linesep)



