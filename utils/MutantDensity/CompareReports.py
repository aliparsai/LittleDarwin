import sys

reportFileHandleDict = dict()
for reportArg in sys.argv[1:]:
    reportFile, reportName = reportArg.split(',')
    reportFileHandleDict[reportName] = open(reportFile, 'r')

reportValuesDict = dict()


for reportName in reportFileHandleDict.keys():
    reportValuesDict[reportName] = dict()
    for line in reportFileHandleDict[reportName]:
        name, value = line.strip('\n').split(',')
        reportValuesDict[reportName][name] = value

names = set()
for reportName in reportFileHandleDict.keys():
    names.update(set(reportValuesDict[reportName].keys()))

with open("result.csv", 'w') as result:
    result.write("Name")
    for reportName in reportFileHandleDict.keys():
        result.write(',' + reportName)
    result.write('\n')

    namesList = sorted(list(names))
    for name in namesList:
        result.write(name)
        for reportName in reportFileHandleDict.keys():
            result.write(',' + (reportValuesDict[reportName][name] if name in reportValuesDict[reportName].keys() else '0'))
        result.write('\n')
