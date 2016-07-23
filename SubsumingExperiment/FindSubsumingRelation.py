import fnmatch
import os
import sys
import shelve

from RetrieveLineCoverageFromCloverXML import CloverXMLReportParser


class Mutant(object):
    def __init__(self):
        self.id = None
        self.isSubsuming = False
        self.isRedundant = False
        self.path = None
        self.cuPath = None
        self.covered = -1
        self.lineNumber = -1
        self.failedTests = set()
        self.subsumedby = set()
        self.subsumes = set()
        # self.redundant = set()


    def getCoverageInfo(self, cloverXMLReportParserInstance):
        assert isinstance(cloverXMLReportParserInstance, CloverXMLReportParser)
        assert self.lineNumber >= 0
        self.covered = int(cloverXMLReportParserInstance.findCoverage(self.cuPath, self.lineNumber))

    def getBuildResultFilePath(self):
        return ".txt".join(self.path.rsplit('.java', 1))

    def __str__(self):
        return " ".join(str(x) for x in ["Mutant ", self.id, "| Path:", self.path, "| Subsuming:", self.subsuming, "| Covered:", self.covered])


class MutantSet(object):
    def __init__(self, globalPath, coverageReportPath):
        self.globalPath = globalPath
        self.coverageReportPath = coverageReportPath
        self.mutants = list()
        self.filteredMutants = list()
        self.redundancyClusters = dict()
        assert os.path.exists(coverageReportPath)

        self.cloverXMLReportParserInstance = CloverXMLReportParser(coverageReportPath)

    def retrieveMutants(self):
        for root, dirnames, filenames in os.walk(os.path.join(self.globalPath, self.path)):
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
                newMutant.getCoverageInfo(self.cloverXMLReportParserInstance)

                self.mutants.append(newMutant)

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

            if mutant1.failedTests < mutant2.failedTests:
                mutant1.subsumes.add(mutant2)
                mutant2.subsumedby.add(mutant1)

            if mutant1.failedTests == mutant2.failedTests:
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
            if len(mutant.subsumedby) == 0:
                mutant.isSubsuming = True

    def filterMutants(self):
        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            if not len(mutant.failedTests) == 0 and not mutant.isRedundant:
                self.filteredMutants.append(mutant)

        checkedCUs = set()
        for cluster in self.redundancyClusters.items():
            assert isinstance(cluster, set)
            for mutant in cluster:
                assert isinstance(mutant, Mutant)
                if mutant.cuPath not in checkedCUs:
                    checkedCUs.add(mutant.cuPath)
                    assert mutant not in self.filteredMutants
                    self.filteredMutants.append(mutant)





