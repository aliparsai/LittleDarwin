import fnmatch
import itertools
import os
import sys


class Mutant(object):
    def __init__(self):
        self.id = None
        self.type = None
        self.isSubsuming = False
        self.path = None
        self.cuPath = None
        self.lineNumber = -1
        self.failedTests = set()
        self.subsumedby = set()
        self.subsumes = set()
        self.mutuallySubsuming = set()
        self.globalPath = None

    def toCSV(self, short=True):
        appStr = lambda l, q: l.append(str(q)) if " " not in str(q) else l.append("\"" + str(q) + "\"")

        values = list()
        appStr(values, self.id)
        appStr(values, self.type)
        appStr(values, self.path)
        appStr(values, self.cuPath)
        appStr(values, self.lineNumber)
        appStr(values, self.isSubsuming)
        appStr(values, len(self.failedTests))
        if not short:
            appStr(values, self.failedTests)

        appStr(values, ";".join([str(x.id) for x in self.subsumes]))
        appStr(values, ";".join([str(x.id) for x in self.subsumedby]))
        appStr(values, ";".join([str(x.id) for x in self.mutuallySubsuming]))

        return ",".join(values)

    def getBuildResultFilePath(self):
        return ".txt".join(self.path.rsplit('.java', 1))

    def __str__(self):
        return " ".join(str(x) for x in
                        ["Mutant ", self.id, ":", self.type, "| File:", os.path.basename(self.cuPath), "| Subsuming:",
                         self.isSubsuming])

    def __repr__(self):
        return self.__str__()


class MutantSet(object):
    def __init__(self, globalPath=None):
        self.globalPath = None if globalPath is None else os.path.abspath(globalPath)
        self.mutants = list()

    def __str__(self):
        lines = [str(m) for m in self.mutants]
        return "\n".join(lines)

    def __add__(self, other):
        tmpMSet = MutantSet()
        tmpMSet.mutants.extend(self.mutants)
        tmpMSet.mutants.extend(other.mutants)
        return tmpMSet

    def printSubsuming(self):
        lines = [str(m) for m in self.mutants if m.isSubsuming is True]
        return "\n".join(lines)

    def toCSV(self, fileHandle=sys.stdout, short=True):
        assert isinstance(fileHandle, file)

        numMutants = len(self.mutants)

        mutantIndex = 0
        fileHandle.write("MutantSet\r\nField,Value\r\nGlobalPath," + str(self.globalPath))
        fileHandle.write("\r\nNumberOfMutants," + str(numMutants) + "\r\n\r\nMutants\r\n")

        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            mutantIndex += 1
            mutant.id = mutantIndex

        if short:
            fileHandle.write(
                "\"Mutant ID\",\"Mutant Type\",\"Mutant Path\",\"CompilationUnit Path\",\"Line Number\",\"isSubsuming\",\"Number of Failed Tests\",\"Subsumes\",\"SubsumedBy\",\"MutuallySubsuming\"\r\n")
        else:
            fileHandle.write(
                "\"Mutant ID\",\"Mutant Type\",\"Mutant Path\",\"CompilationUnit Path\",\"Line Number\",\"isSubsuming\",\"Number of Failed Tests\",\"Failed Tests\",\"Subsumes\",\"SubsumedBy\",\"MutuallySubsuming\"\r\n")

        for mutant in self.mutants:
            fileHandle.write(mutant.toCSV(short) + "\r\n")

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
                newMutant.globalPath = self.globalPath

                self.mutants.append(newMutant)
                counter += 1
                # sys.stdout.write(str(counter) + "       \r")
                # sys.stdout.flush()

    def retrieveFailedTestResults(self):
        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            record = False
            failedTestResultList = list()
            with open(os.path.join(mutant.globalPath, mutant.getBuildResultFilePath()), "rU") as buildResultFileHandle:
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

        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            if len(mutant.subsumedby - mutant.mutuallySubsuming) == 0 and len(mutant.failedTests) > 0:
                mutant.isSubsuming = True


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
        if self.mutants <= (mutant.mutuallySubsuming | {mutant}):
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

        if me.failedTests < him.failedTests:
            return True

        return False


class MutantSubsumptionGraphEdge(object):
    newID = itertools.count().next

    def __init__(self, subsuming=None, subsumed=None):
        self.id = MutantSubsumptionGraphEdge.newID()
        self.mutantSubsuming = subsuming
        self.mutantSubsumed = subsumed

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
                    newEdge = MutantSubsumptionGraphEdge(node1, node2)
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
    mutantSet.predictedMutantSubsumptionGraph = MutantSubsumptionGraph()

    counter = 0
    total = len(mutantSet.mutants)

    for mutant in mutantSet.mutants:
        counter += 1
        # sys.stdout.write(str(counter) + "/" + str(total) + "N")
        mutantSet.mutantSubsumptionGraph.addMutant(mutant)
        # sys.stdout.write("P")
        mutantSet.predictedMutantSubsumptionGraph.addMutant(mutant)
        # sys.stdout.write("        \r")
        # sys.stdout.flush()


def getStatsforMutantList(mList):
    typeDict = dict()
    for mutant in mList:
        assert isinstance(mutant, Mutant)
        if mutant.type in typeDict.keys():
            typeDict[mutant.type] += 1

        else:
            typeDict[mutant.type] = 1

    return typeDict


if __name__ == "__main__":
    mutantSets = [MutantSet(ms) for ms in sys.argv[1:]]

    fSet = MutantSet()
    for mSet in mutantSets:
        mSet.retrieveMutants()
        fSet += mSet

    fSet.assignStatus()
    normalDist = getStatsforMutantList(fSet.mutants)
    subsumingMutants = [m for m in fSet.mutants if m.isSubsuming is True]
    subsumingDist = getStatsforMutantList(subsumingMutants)

    # print "total:", len(fSet.mutants), "| subsuming:", len(subsumingMutants)
    print "Mutation Operator,All,Subsuming"
    sortedKeys = sorted([k for k in normalDist.keys() if "null" not in str.lower(k)])
    sortedKeys.extend(sorted([k for k in normalDist.keys() if "null" in str.lower(k)]))

    # print sortedKeys

    for t in sortedKeys:
#       print str(t) + "," + str(normalDist[t]) + ",{0:.2f}%".format(
#           normalDist[t] * 100.0 / len(fSet.mutants)) + (",0,0%" if t not in subsumingDist.keys() else "," + str(
#           subsumingDist[t]) + ",{0:.2f}%".format(subsumingDist[t] * 100.0 / len(subsumingMutants)))

        print str(t) + "," + str(normalDist[t]) + (",0" if t not in subsumingDist.keys() else "," + str(
            subsumingDist[t]))

    print ",,"
    print "Total," + str(len(fSet.mutants)) + "," + str(len(subsumingMutants))

