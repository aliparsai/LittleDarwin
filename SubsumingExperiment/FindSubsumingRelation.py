import os
import sys
import shelve


def retrieveFailedTestResults(mutationDatabase):

    failedTestResult = dict()

    mutantList = list()
    buildResultList = list()

    for compilationUnit in mutationDatabase.keys():
        for mutant in mutationDatabase[compilationUnit]:
            mutantList.append(str(mutant))
            buildResultList.append('.txt'.join(str(mutant).rsplit('.java', 1)))

    for buildResultFile in buildResultList:
        record = False
        failedTestResultList = list()
        with open(os.path.join(sys.argv[1], buildResultFile), "rU") as buildResultFileHandle:
            for line in buildResultFileHandle:

                if "Tests run:" in line:
                    record = False

                if record:
                    strippedLine = line.strip().split(':')[0]
                    if ' ' not in strippedLine and "test" in strippedLine.lower():
                        failedTestResultList.append(strippedLine)

                if ("Failed tests:" in line) or ("Tests in error:" in line):
                    record = True

        failedTestResult[buildResultFile] = set(failedTestResultList)

    return failedTestResult

def killedMutantsByTests(failedTestResult):
    assert isinstance(failedTestResult, dict)
    testSet = dict()

    for mutant in failedTestResult.keys():
        # print mutant
        for test in failedTestResult[mutant]:
            # print test
            if not testSet.has_key(test):
                testSet[test] = [ mutant ]

            else:
                testSet[test].append(mutant)

    return testSet


mutationDatabase = shelve.open(os.path.join(sys.argv[1], "mutationdatabase"), "r")

failedTestResult = retrieveFailedTestResults(mutationDatabase)
testSets = killedMutantsByTests(failedTestResult)

subsumes = dict()
subsumedby = dict()
for key in failedTestResult.keys():
    subsumedby[key] = set()
    subsumes[key] = set()

for key1 in failedTestResult.keys():
    for key2 in failedTestResult.keys():
        if key1 == key2 or len(failedTestResult[key1]) == 0 or len(failedTestResult[key2]) == 0:
            continue

        mutant1 = failedTestResult[key1]
        mutant2 = failedTestResult[key2]

        assert isinstance(mutant1, set)
        assert isinstance(mutant2, set)

        if mutant1 < mutant2:
            subsumes[key1].add(key2)
            subsumedby[key2].add(key1)

        # if mutant1 == mutant2:
        #     print key1, key2
#
for key in sorted(failedTestResult.keys()):
    numberOfSubsumed = len(subsumedby[key])
    numberOfSubsumes = len(subsumes[key])

    # if numberOfSubsumed == 0:
    #     print key

    print key, numberOfSubsumed, numberOfSubsumes


