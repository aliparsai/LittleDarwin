import fnmatch
import os
import sys
import itertools

import time

from RetrieveLineCoverageFromCloverXML import CloverXMLReportParser
from RetrieveLineCoverageFromCloverDB import CloverDBParser

class Mutant(object):
    def __init__(self):
        self.id = None
        self.type = None
        self.isSubsuming = False
        self.isProbablySubsuming = False
        self.isRedundant = False
        self.isProbablyRedundant = False
        self.path = None
        self.cuPath = None
        self.executionCount = -1
        self.coveringTestsCount = -1
        self.lineNumber = -1
        self.failedTests = set()
        self.coveringTests = set()
        self.subsumedby = set()
        self.subsumes = set()
        self.probablySubsumes = set()
        self.probablySubsumedby = set()
        self.mutuallySubsuming = set()
        self.probablyMutuallySubsuming = set()
        # self.redundant = set()

    def toCSV(self, short=True):
        appStr = lambda l, q: l.append(str(q)) if " " not in str(q) else l.append("\"" + str(q) + "\"")

        values = list()
        appStr(values, self.id)
        appStr(values, self.type)
        appStr(values, self.path)
        appStr(values, self.cuPath)
        appStr(values, self.lineNumber)
        appStr(values, self.isSubsuming)
        appStr(values, self.isProbablySubsuming)
        appStr(values, len(self.failedTests))
        if not short:
            appStr(values, self.failedTests)
        appStr(values, len(self.coveringTests))
        if not short:
            appStr(values, self.coveringTests)
        appStr(values, ";".join([str(x.id) for x in self.subsumes]))
        appStr(values, ";".join([str(x.id) for x in self.subsumedby]))
        appStr(values, ";".join([str(x.id) for x in self.probablySubsumes]))
        appStr(values, ";".join([str(x.id) for x in self.probablySubsumedby]))
        appStr(values, ";".join([str(x.id) for x in self.mutuallySubsuming]))
        appStr(values, ";".join([str(x.id) for x in self.probablyMutuallySubsuming]))

        return ",".join(values)

    def getCoverageInfo(self, cloverXMLReportParserInstance, cloverDBParserInstance, clientMode=False):
        assert isinstance(cloverXMLReportParserInstance, CloverXMLReportParser)
        assert isinstance(cloverDBParserInstance, CloverDBParser)
        assert self.lineNumber >= 0
        self.executionCount = int(cloverXMLReportParserInstance.findCoverage(self.cuPath, self.lineNumber))
        self.coveringTestsCount, self.coveringTests = cloverDBParserInstance.findCoverage(self.cuPath, self.lineNumber, clientMode)


    def getBuildResultFilePath(self):
        return ".txt".join(self.path.rsplit('.java', 1))

    def outputForWeka(self):
        return ",".join(str(x) for x in [self.isSubsuming, self.isRedundant, self.type, self.executionCount, self.coveringTestsCount])

    def __str__(self):
        return " ".join(str(x) for x in ["Mutant ", self.id, "| File:", os.path.basename(self.cuPath), "| Subsuming:",
                                         self.isSubsuming,  "| Redundant:", self.isRedundant, "| Covered:", self.executionCount])

    def __repr__(self):
        return self.__str__()


class MutantSet(object):
    def __init__(self, globalPath, coverageReportPath, coverageDBPath, javaHandler):
        self.globalPath = globalPath
        self.coverageReportPath = coverageReportPath
        self.coverageDBPath = coverageDBPath
        self.mutants = list()
        self.filteredMutants = list()
        self.redundancyClusters = dict()
        self.redundancyClustersFromCoverage = dict()

        assert os.path.exists(coverageReportPath)
        assert os.path.exists(coverageDBPath)

        self.cloverXMLReportParserInstance = CloverXMLReportParser(coverageReportPath)
        self.cloverDBParserInstance = CloverDBParser(coverageDBPath, javaHandler)

    def __del__(self):
        self.cloverDBParserInstance.gateway.close()
        del self.cloverDBParserInstance
        del self.cloverXMLReportParserInstance

    def toCSV(self, fileHandle=sys.stdout, short=True):
        assert isinstance(fileHandle, file)

        numMutants = len(self.mutants)

        mutantIndex = 0
        fileHandle.write("MutantSet\r\nField,Value\r\nGlobalPath,"+str(self.globalPath)+"\r\nCoverageReportPath,")
        fileHandle.write(str(self.coverageReportPath)+"\r\nCoverageDBPath,"+str(self.coverageDBPath))
        fileHandle.write("\r\nNumberOfMutants,"+str(numMutants)+"\r\n\r\nMutants\r\n")

        for mutant in self.mutants:
            assert isinstance(mutant,Mutant)
            mutantIndex += 1
            mutant.id = mutantIndex

        if short:
            fileHandle.write("\"Mutant ID\",\"Mutant Type\",\"Mutant Path\",\"CompilationUnit Path\",\"Line Number\",\"isSubsuming\",\"isProbablySubsuming\",\"Number of Failed Tests\",\"Number of Covering Tests\",\"Subsumes\",\"SubsumedBy\",\"ProbablySubsumes\",\"ProbablySubsumedBy\",\"MutuallySubsuming\",\"ProbablyMutuallySubsuming\"\r\n")
        else:
            fileHandle.write("\"Mutant ID\",\"Mutant Type\",\"Mutant Path\",\"CompilationUnit Path\",\"Line Number\",\"isSubsuming\",\"isProbablySubsuming\",\"Number of Failed Tests\",\"Failed Tests\",\"Number of Covering Tests\",\"Covering Tests\",\"Subsumes\",\"SubsumedBy\",\"ProbablySubsumes\",\"ProbablySubsumedBy\",\"MutuallySubsuming\",\"ProbablyMutuallySubsuming\"\r\n")

        for mutant in self.mutants:
            fileHandle.write(mutant.toCSV(short)+"\r\n")

    def outputForWeka(self, skipHeader=False):
        lines = list()
        if not skipHeader:
            lines.append("\n\n% generated by FindSubsumingRelation script %")
            lines.append("% (c) 2016 Ali Parsai --- www.parsai.net    %")
            lines.append("\n\n\n")
            lines.append("@relation \'subsuming\'")
            lines.append("@attribute \'IsSubsuming\' { \'True\', \'False\' }")
            lines.append("@attribute \'IsRedundant\' { \'True\', \'False\' }")
            lines.append("@attribute \'MutantType\' { \'arithmeticOperatorReplacementBinary\', \'arithmeticOperatorReplacementShortcut\', \'arithmeticOperatorReplacementUnary\', \'logicalOperatorReplacement\', \'shiftOperatorReplacement\', \'relationalOperatorReplacement\', \'conditionalOperatorReplacement\', \'conditionalOperatorDeletion\', \'assignmentOperatorReplacementShortcut\' }")
            lines.append("@attribute \'TimesCovered\' numeric")
            lines.append("@attribute \'NumberOfFailedTests\' numeric")
            lines.append("\n\n@data\n")

        for mutant in self.filteredMutants:
            lines.append(mutant.outputForWeka())

        return "\n".join(lines)

    def retrieveMutants(self):
        counter = 0
        for root, dirnames, filenames in os.walk(self.globalPath):
            for filename in fnmatch.filter(filenames, "*.java"):
                if str(filename) == "original.java":
                    continue
                newMutant = Mutant()
                newMutant.path = os.path.relpath(os.path.join(root, filename), self.globalPath)
                newMutant.cuPath = os.path.dirname(newMutant.path)
                newMutant.id = int(str(filename).rsplit(".java", 1)[0])

                with open(os.path.join(root, filename), "r") as mutantHandle:
                    mutantContent = mutantHandle.readlines()

                mutantLine = None
                for line in mutantContent:
                    if "----> line number in original file:" in line:
                        mutantLine = line
                        break

                assert mutantLine is not None
                newMutant.lineNumber = int(mutantLine.rsplit(":", 1)[1])

                mutantLine = None
                for line in mutantContent:
                    if "mutant type: " in line:
                        mutantLine = line
                        break

                assert mutantLine is not None
                newMutant.type = str(mutantLine.rsplit(": ", 1)[1]).strip()

                newMutant.getCoverageInfo(self.cloverXMLReportParserInstance, self.cloverDBParserInstance, True)

                self.mutants.append(newMutant)
                counter += 1
                sys.stdout.write(str(counter)+"       \r")
                sys.stdout.flush()


    def retrieveFailedTestResults(self):
        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            record = False
            failedTestResultList = list()
            with open(os.path.join(self.globalPath, mutant.getBuildResultFilePath()), "rU") as buildResultFileHandle:
                for line in buildResultFileHandle:

                    if "Tests run:" in line:
                        record = False

                    if record:
                        strippedLine = line.strip().split(':')[0]
                        if ' ' not in strippedLine and "test" in strippedLine.lower():
                            failedTestResultList.append(strippedLine)

                    if ("Failed tests:" in line) or ("Tests in error:" in line):
                        record = True

            mutant.failedTests = set(failedTestResultList)

    def assignStatus(self):
        self.retrieveFailedTestResults()

        for mutant1 in self.mutants:
            for mutant2 in self.mutants:
                assert isinstance(mutant1, Mutant)
                assert isinstance(mutant2, Mutant)
                if mutant1 is mutant2 or len(mutant1.failedTests) == 0 or len(mutant2.failedTests) == 0:
                    continue

                if mutant1.failedTests <= mutant2.failedTests:
                    mutant1.subsumes.add(mutant2)
                    mutant2.subsumedby.add(mutant1)

                if mutant1.failedTests == mutant2.failedTests:
                    mutant1.mutuallySubsuming.add(mutant2)
                    mutant2.mutuallySubsuming.add(mutant1)
                    if self.redundancyClusters.has_key(frozenset(mutant1.failedTests)):
                        assert isinstance(self.redundancyClusters[frozenset(mutant1.failedTests)], set)
                        self.redundancyClusters[frozenset(mutant1.failedTests)].add(mutant1)
                        self.redundancyClusters[frozenset(mutant1.failedTests)].add(mutant2)

                    else:
                        self.redundancyClusters[frozenset(mutant1.failedTests)] = {mutant1, mutant2}

                    mutant1.isRedundant = True
                    mutant2.isRedundant = True

        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            if len(mutant.subsumedby - mutant.mutuallySubsuming) == 0 and len(mutant.failedTests) > 0:
                mutant.isSubsuming = True

    def similarityFunction(self, testSet1, testSet2):
        assert isinstance(testSet1, set)
        assert isinstance(testSet2, set)

        intersection = testSet1 & testSet2
        testSet1Remainder = testSet1 - intersection
        testSet2Remainder = testSet2 - intersection

        if len(testSet1Remainder) > len(testSet2Remainder):
            return 0.0

        score = len(intersection) / float(len(testSet1))
        # print score
        return score

    def predictStatus(self, threshold=1.0):
        for mutant1 in self.mutants:
            for mutant2 in self.mutants:
                assert isinstance(mutant1, Mutant)
                assert isinstance(mutant2, Mutant)
                if mutant1 is mutant2 or len(mutant1.coveringTests) == 0 or len(mutant2.coveringTests) == 0:
                    continue

                if self.similarityFunction(mutant1.coveringTests, mutant2.coveringTests) >= threshold:
                    mutant1.probablySubsumes.add(mutant2)
                    mutant2.probablySubsumedby.add(mutant1)

                if mutant1.coveringTests == mutant2.coveringTests:
                    mutant1.probablyMutuallySubsuming.add(mutant2)
                    mutant2.probablyMutuallySubsuming.add(mutant1)
                    if self.redundancyClustersFromCoverage.has_key(frozenset(mutant1.coveringTests)):
                        assert isinstance(self.redundancyClustersFromCoverage[frozenset(mutant1.coveringTests)], set)
                        self.redundancyClustersFromCoverage[frozenset(mutant1.coveringTests)].add(mutant1)
                        self.redundancyClustersFromCoverage[frozenset(mutant1.coveringTests)].add(mutant2)

                    else:
                        self.redundancyClustersFromCoverage[frozenset(mutant1.coveringTests)] = {mutant1, mutant2}

                    mutant1.isProbablyRedundant = True
                    mutant2.isProbablyRedundant = True

        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            if len(mutant.probablySubsumedby - mutant.probablyMutuallySubsuming) == 0 and len(mutant.coveringTests) > 0:
                mutant.isProbablySubsuming = True

    def filterMutants(self):
        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            if not len(mutant.failedTests) == 0 and not mutant.isRedundant:
                self.filteredMutants.append(mutant)

        for cluster in self.redundancyClusters.values():
            assert isinstance(cluster, set)
            checkedCUs = set()
            for mutant in cluster:
                assert isinstance(mutant, Mutant)
                if mutant.cuPath not in checkedCUs:
                    checkedCUs.add(mutant.cuPath)
                    assert mutant not in self.filteredMutants
                    self.filteredMutants.append(mutant)

    def resetPredictions(self):
        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            mutant.isProbablyRedundant = False
            mutant.isProbablySubsuming = False


class MutantSubsumptionGraphNode(object):
    newID = itertools.count().next

    def __init__(self, predicted=False):
        self.id = MutantSubsumptionGraphNode.newID()
        self.mutants = set()
        self.predicted = predicted

    def __eq__(self, other):
        assert isinstance(other, MutantSubsumptionGraphNode)
        if self.mutants == other.mutants:
            return True
        return False

    def addMutant(self, mutant):
        assert isinstance(mutant, Mutant)
        if not self.predicted:
            if self.mutants <= (mutant.mutuallySubsuming | {mutant}):
                self.mutants.add(mutant)
                return 1
        else:
            if self.mutants <= (mutant.probablyMutuallySubsuming | {mutant}):
                self.mutants.add(mutant)
                return 1
        return 0

    def checkSubsuming(self, node):
        assert isinstance(node, MutantSubsumptionGraphNode)
        if len(node.mutants) <= 0 or len(self.mutants) <= 0:
            return 0

        me = list(self.mutants)[0]
        him = list(node.mutants)[0]

        assert isinstance(me, Mutant)
        assert isinstance(him, Mutant)

        if not self.predicted:
            if me.failedTests < him.failedTests:
                return True
        else:
            if me.coveringTests < him.coveringTests:
                return True
        return False


class MutantSubsumptionGraphEdge(object):
    newID = itertools.count().next

    def __init__(self, subsuming=None, subsumed=None, predicted=False):
        self.id = MutantSubsumptionGraphEdge.newID()
        self.mutantSubsuming = subsuming
        self.mutantSubsumed = subsumed
        self.predicted = predicted

    def __eq__(self, other):
        assert isinstance(other, MutantSubsumptionGraphEdge)
        if self.mutantSubsuming is other.mutantSubsuming and self.mutantSubsumed is other.mutantSubsumed:
            return True
        return False


class MutantSubsumptionGraph(object):
    def __init__(self, predicted=False):
        self.nodes = list()
        self.edges = list()
        self.predicted = predicted

    def __sub__(self, other):
        tp, fp, fn = self.calculateConfusionMatrix(other)
        return fp + fn


    def calculateConfusionMatrix(self, other):
        assert isinstance(other, MutantSubsumptionGraph)
        assert len(self.nodes) == len(other.nodes)
        for node in self.nodes:
            found = False
            for otherNode in other.nodes:
                if node == otherNode:
                    found = True
                    break
            assert found is True

        truePositive = 0
        falsePositive = 0
        falseNegative = 0
        marked = list()
        markedOther = list()

        for edge in self.edges:
            found = False
            for otherEdge in other.edges:
                if edge == otherEdge:
                    found = True
                    break

            if found is True:
                truePositive += 1
                marked.append(edge)
                markedOther.append(otherEdge)

        for edge in self.edges:
            if edge not in marked:
                falseNegative += 1

        for edgeOther in other.edges:
            if edgeOther not in markedOther:
                falsePositive += 1

        return truePositive, falsePositive, falseNegative

    def addMutant(self, mutant):
        assert isinstance(mutant, Mutant)
        addCounter = 0

        for node in self.nodes:
            assert isinstance(node, MutantSubsumptionGraphNode)
            addCounter += node.addMutant(mutant)

        assert addCounter <= 1
        if addCounter == 0:
            newNode = MutantSubsumptionGraphNode(self.predicted)
            newNode.addMutant(mutant)
            self.nodes.append(newNode)

        for node1 in self.nodes:
            assert isinstance(node1, MutantSubsumptionGraphNode)

            for node2 in self.nodes:
                assert isinstance(node2, MutantSubsumptionGraphNode)

                if node1 is node2:
                    continue

                if node1.checkSubsuming(node2):
                    newEdge = MutantSubsumptionGraphEdge(node1, node2, self.predicted)
                    exists = False

                    for edge in self.edges:
                        if newEdge == edge:
                            exists = True
                            break

                    if not exists:
                        self.edges.append(newEdge)


def createMutantSubsumptionGraph(mutantSet):
    assert isinstance(mutantSet, MutantSet)
    mutantSet.mutantSubsumptionGraph = MutantSubsumptionGraph()
    mutantSet.predictedMutantSubsumptionGraph = MutantSubsumptionGraph(predicted=True)

    counter = 0
    total = len(mutantSet.mutants)

    for mutant in mutantSet.mutants:
        counter += 1
        sys.stdout.write(str(counter) + "/" + str(total) + "N")
        mutantSet.mutantSubsumptionGraph.addMutant(mutant)
        sys.stdout.write("P")
        mutantSet.predictedMutantSubsumptionGraph.addMutant(mutant)
        sys.stdout.write("        \r")
        sys.stdout.flush()


def printResults(mutantSet):
    assert isinstance(mutantSet, MutantSet)

    truePositiveSubsuming = 0
    trueNegativeSubsuming = 0
    falsePositiveSubsuming = 0
    falseNegativeSubsuming = 0

    truePositiveRedundant = 0
    trueNegativeRedundant = 0
    falsePositiveRedundant = 0
    falseNegativeRedundant = 0

    for mutant in mutantSet.mutants:
        assert isinstance(mutant, Mutant)
        if mutant.isProbablySubsuming and mutant.isSubsuming:
            truePositiveSubsuming += 1
        elif mutant.isProbablySubsuming and not mutant.isSubsuming:
            falsePositiveSubsuming += 1
        elif not mutant.isProbablySubsuming and mutant.isSubsuming:
            falseNegativeSubsuming += 1
        elif not mutant.isProbablySubsuming and not mutant.isSubsuming:
            trueNegativeSubsuming += 1

        if mutant.isProbablyRedundant and mutant.isRedundant:
            truePositiveRedundant += 1
        elif mutant.isProbablyRedundant and not mutant.isRedundant:
            falsePositiveRedundant += 1
        elif not mutant.isProbablyRedundant and mutant.isRedundant:
            falseNegativeRedundant += 1
        elif not mutant.isProbablyRedundant and not mutant.isRedundant:
            trueNegativeRedundant += 1

    totalMutants = len(mutantSet.mutants)
    assert totalMutants == truePositiveSubsuming + falsePositiveSubsuming + trueNegativeSubsuming + falseNegativeSubsuming
    assert totalMutants == truePositiveRedundant + falsePositiveRedundant + trueNegativeRedundant + falseNegativeRedundant

    precisionSubsuming = 100 * truePositiveSubsuming / float(truePositiveSubsuming + falsePositiveSubsuming)
    recallSubsuming = 100 * truePositiveSubsuming / float(truePositiveSubsuming + falseNegativeSubsuming)
    accuracySubsuming = 100 * (truePositiveSubsuming + trueNegativeSubsuming) / float(totalMutants)

    # precisionRedundant = 100 * truePositiveRedundant / float(truePositiveRedundant + falsePositiveRedundant)
    # recallRedundant = 100 * truePositiveRedundant / float(truePositiveRedundant + falseNegativeRedundant)
    # accuracyRedundant = 100 * (truePositiveRedundant + trueNegativeRedundant) / float(totalMutants)

    print "Subsuming Prediction:", len(
        mutantSet.mutants), "\nTP:", truePositiveSubsuming, " FP:", falsePositiveSubsuming, "\nFN:", falseNegativeSubsuming, "TN:", trueNegativeSubsuming
    print "----------------------------\nPrecision: %.2f" % precisionSubsuming, "\nRecall: %.2f" % recallSubsuming, "\nAccuracy: %.2f" % accuracySubsuming, "\n****************************"

    # print "Graph Distance:"
    # print mSet.mutantSubsumptionGraph.calculateConfusionMatrix(mSet.predictedMutantSubsumptionGraph)

    #
    # print "Redundant Prediction:", len(
    #     mSet.mutants), "\nTP:", truePositiveRedundant, " FP:", falsePositiveRedundant, "\nFN:", falseNegativeRedundant, "TN:", trueNegativeRedundant
    # print "----------------------------\nPrecision: %.2f" % precisionRedundant, "\nRecall: %.2f" % recallRedundant, "\nAccuracy: %.2f" % accuracyRedundant, "\n****************************"



if __name__ == "__main__":

    mutantSet = MutantSet(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

    mutantSet.retrieveMutants()
    mutantSet.assignStatus()
    mutantSet.predictStatus(1.0)

    printResults(mutantSet)
    print "Strong:\n-------------------------------"

    freeFile = 0

    while os.path.exists("single-{0:05d}.csv".format(freeFile)):
        freeFile += 1

    csvFile = open("single-{0:05d}.csv".format(freeFile), "w")

    mutantSet.toCSV(csvFile, True)

    csvFile.close()

    del mutantSet
    time.sleep(2)


