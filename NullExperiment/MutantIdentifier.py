import fnmatch
import sys
import os


class Mutant(object):
    def __init__(self):
        self.id = None
        self.node = None
        self.lineNumber = None
        self.type = None
        self.status = 999     # 0 unknown, 1 survived, -1 killed, 999 unset
        self.path = None

    def __str__(self):
        return " ".join(str(x) for x in ["Mutant ", self.id, "| Path:", self.path, "| Status:", self.status, "| Node:", self.node, "| Line:", self.lineNumber])


class JavaClass(object):
    def __init__(self, name, path, globalPath):
        self.name = None
        self.path = None
        self.globalPath = None
        self.mutants = list()
        self.types = set()
        self.survived = 0
        self.killed = 0
        self.retrieveMutants()
        self.getAllTypes()
        self.getMutantStats()

    def findMutantByNode(self, nodeID):
        for mutant in self.mutants:
            if nodeID in mutant.nodes:
                return mutant

    def findMutantByID(self, ID):
        for mutant in self.mutants:
            if ID == mutant.id:
                return mutant

    def findMutantsByLN(self, ln):
        result = list()
        for mutant in self.mutants:
            if ln == mutant.lineNumber:
                result.append(mutant)

        return result

    def findMutantsByType(self, t):
        result = list()
        for mutant in self.mutants:
            if t == mutant.type:
                result.append(mutant)

        return result

    def getAllTypes(self):
        for mutant in self.mutants:
            self.types.add(mutant)

    def getMutantStatsByType(self):
        stats = dict()

        for t in self.types:
            stats[t] = 0, 0, 0

        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            survived, killed, total = stats[mutant.type]
            total += 1
            survived += 1 if mutant.status == 1 else 0
            killed += 1 if mutant.status == -1 else 0
            stats[mutant.type] = survived, killed, total
            assert survived + killed == total

        return stats

    def getMutantStats(self):
        total = 0
        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            total += 1
            self.survived += 1 if mutant.status == 1 else 0
            self.killed += 1 if mutant.status == -1 else 0
            assert self.survived + self.killed == total

    def retrieveMutants(self):
        for root, dirnames, filenames in os.walk(os.path.join(self.globalPath, self.path)):
            for filename in fnmatch.filter(filenames, "*.java"):
                if str(filename) == "original.java":
                    continue
                newMutant = Mutant()
                newMutant.path = os.path.relpath(os.path.join(root, filename), self.globalPath)
                newMutant.id = int(str(filename).rsplit(".java", 1)[0])

                with open(os.path.join(root, filename), "r") as mutantHandle:
                    mutantContent = mutantHandle.readlines()

                gotLine = False
                gotNode = False
                gotType = False

                for line in mutantContent:
                    if not gotLine and "----> line number in original file:" in line:
                        newMutant.lineNumber = int(line.split(":", 1)[1].strip())
                        gotLine = True

                    if not gotNode and "----> mutated nodes:" in line:
                        newMutant.node = int(line.split(":", 1)[1].strip())
                        gotNode = True

                    if not gotType and "mutant type:" in line:
                        newMutant.type = str(line.split("type:", 1)[1].strip())
                        gotType = True

                    if gotNode and gotLine and gotType:
                        break

                with open(os.path.join(self.globalPath, "report.txt")) as reportHandle:
                    reportContent = reportHandle.readlines()

                for line in reportContent:
                    splittedLine = line.split(":", 1)
                    if splittedLine[0] == self.path:
                        parse = splittedLine[1].split(" - killed (")
                        if "\'" + filename + "\'" in parse[0]:
                            newMutant.status = 1
                        elif "\'" + filename + "\'" in parse[1]:
                            newMutant.status = -1
                        else:
                            newMutant.status = 0
                        break

                self.mutants.append(newMutant)

class JavaProject(object):
    def __init__(self, searchPath):
        self.searchPath = searchPath
        self.classList = list()
        self.listClasses()

    def listClasses(self):
        for root, dirnames, filenames in os.walk(self.searchPath):
            for dirname in fnmatch.filter(dirnames, "*.java"):
                path = os.path.relpath(os.path.join(root, dirname), self.searchPath)
                name = path.replace('/', '.').rsplit(".java", 1)[0]
                globalPath = self.searchPath

                newClass = JavaClass(name, path, globalPath)
                self.classList.append(newClass)

    def getClassByName(self, className):
        for c in self.classList:
            assert isinstance(c, JavaClass)
            if c.name == className:
                return c
        return None

    def getStatsByType(self):
        total = dict()

        for c in self.classList:
            assert isinstance(c,JavaClass)
            stats = c.getMutantStatsByType()
            for k in stats.keys():
                if k not in total:
                    total[k] = 0, 0, 0

                survived, killed, total = stats[k]
                totalSurvived, totalKilled, totalTotal = total[k]

                total[k] = totalSurvived + survived, totalKilled + killed, totalTotal + total

        return total


    def getStatsByClass(self):
        total = dict()

        for c in self.classList:
            assert isinstance(c, JavaClass)

            total[c.name] = c.survived, c.killed, len(c.mutants)

        return total


if __name__ == "__main__":


    if len(sys.argv) < 4:
        print("""
    MutantIdentifier by Ali Parsai

    Usage: {} [NormalPath] [NullPath] [ProjectName]


        """.format(os.path.basename(sys.argv[0])))

        sys.exit(0)

    normalPath = sys.argv[1]
    nullPath = sys.argv[2]
    projectName = sys.argv[3]

    if not os.path.isdir(normalPath) or not os.path.isfile(os.path.join(normalPath, "report.txt")):
        print("Error: NormalPath Incorrect.", normalPath)
        sys.exit(1)

    if not os.path.isdir(nullPath) or not os.path.isfile(os.path.join(nullPath, "report.txt")):
        print("Error: NullPath Incorrect.", nullPath)
        sys.exit(1)

    normalProj = JavaProject(normalPath)
    nullProj = JavaProject(nullPath)

    totalStats = normalProj.getStatsByType()
    totalStats.update(nullProj.getStatsByType())

    typeReport = projectName + "-TypeReport.csv"
    coverageReport = projectName + "-CoverageReport.csv"

    with open(typeReport, "w") as typeReportHandle:
        typeReportHandle.write("Mutation Operator,Survived,Killed,Total")

        for k in totalStats.keys():
            survived, killed, total = totalStats[k]
            line = [k, str(survived), str(killed), str(total)]
            typeReportHandle.write(','.join(line))

    classNameList = set([c.name for c in normalProj.classList])

    lines = list()
    for name in classNameList:
        nullClass = nullProj.getClassByName(name)
        normalClass = normalProj.getClassByName(name)

        lines.append(','.join([name, str(normalClass.survived), str(normalClass.killed), str(len(normalClass.mutants)), str(nullClass.survived), str(nullClass.killed), str(len(nullClass.mutants))]))

    with open(coverageReport, "w") as coverageReportHandle:
        coverageReportHandle.write("Class Name,NormalSurvived,NormalKilled,NormalTotal,NullSurvived,NullKilled,NullTotal")
        coverageReportHandle.writelines(lines)

