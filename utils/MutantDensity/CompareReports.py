import sys

reportFileHandleDict = dict()
for reportArg in sys.argv[1:]:
    reportFile, reportName = reportArg.split(',')
    reportFileHandleDict[reportName] = open(reportFile, 'r')

reportValuesDict = dict()
reportNames = sorted(list(reportFileHandleDict.keys()))


for reportName in reportNames:
    reportValuesDict[reportName] = dict()
    for line in reportFileHandleDict[reportName]:
        name, value = line.strip('\n').split(',')
        reportValuesDict[reportName][name] = value

names = set()
for reportName in reportNames:
    names.update(set(reportValuesDict[reportName].keys()))

with open("result.csv", 'w') as result:
    result.write("Name")
    for reportName in reportNames:
        result.write(',' + reportName)
    result.write('\n')

    namesList = sorted(list(names))
    for name in namesList:
        result.write('.'.join(str(name).split('.java')[0].split('/')))
        for reportName in reportNames:
            result.write(',' + (reportValuesDict[reportName][name] if name in reportValuesDict[reportName].keys() else '0'))
        result.write('\n')
