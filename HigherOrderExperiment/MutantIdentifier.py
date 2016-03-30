import fnmatch
import sys
import os


class Mutant(object):
    def __init__(self):
        self.id = None
        self.nodes = list()
        self.status = 0     # 0 unknown, 1 survived, -1 killed
        self.path = None


class JavaClass(object):
    def __init__(self):
        self.name = None
        self.path = None
        self.globalPath = None
        self.mutants = list()

    def findMutantByNode(self, nodeID):
        for mutant in self.mutants:
            if nodeID in mutant.nodes:
                return mutant


    def findMutantByID(self, ID):
        for mutant in self.mutants:
            if ID == mutant.id:
                return mutant

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

                mutantNodes = None

                for line in mutantContent:
                    if "----> mutated nodes:" in line:
                        mutantNodes = line
                        break
                newMutant.nodes = [int(nodeID) for nodeID in mutantNodes.split(":", 1)[1].split(",")]

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


def listClasses(searchPath):
    classList = list()
    for root, dirnames, filenames in os.walk(searchPath):
        for dirname in fnmatch.filter(dirnames, "*.java"):
            newClass = JavaClass()
            newClass.path = os.path.relpath(os.path.join(root, dirname), searchPath)
            newClass.name = newClass.path.replace('/', '.').rsplit(".java", 1)[0]
            newClass.globalPath = searchPath
            newClass.retrieveMutants()

            classList.append(newClass)

    return classList

def getClassByName(className, classList):
    for c in classList:
        assert isinstance(c, JavaClass)
        if c.name == className:
            return c

if len(sys.argv) < 4:
    print("""
    MutantIdentifier by Ali Parsai

    Usage: {} [FirstOrderPath] [SecondOrderPath] [ReportFile]


    """.format(os.path.basename(sys.argv[0])))

    sys.exit(0)


firstOrderPath = sys.argv[1]
secondOrderPath = sys.argv[2]


if not os.path.isdir(firstOrderPath) or not os.path.isfile(os.path.join(firstOrderPath, "report.txt")):
    print("Error: FirstOrderPath Incorrect.")
    sys.exit(1)


if not os.path.isdir(secondOrderPath) or not os.path.isfile(os.path.join(secondOrderPath, "report.txt")):
    print("Error: SecondOrderPath Incorrect.")
    sys.exit(1)


firstOrderClasses = listClasses(firstOrderPath)
secondOrderClasses = listClasses(secondOrderPath)

classes = list()

for secondOrderClass in secondOrderClasses:
    assert isinstance(secondOrderClass, JavaClass)
    firstOrderClass = getClassByName(secondOrderClass.name, firstOrderClasses)
    if firstOrderClass is None:
        continue
    mutantPairs = dict()
    for secondOrderMutant in secondOrderClass.mutants:
        assert isinstance(secondOrderMutant, Mutant)
        # assert len(firstOrderMutant.nodes == 1)
        firstOrderMutants = list()
        for node in secondOrderMutant.nodes:
            firstOrderMutants.append(firstOrderClass.findMutantByNode(node).id)
        mutantPairs[secondOrderMutant.id] = firstOrderMutants
    classes.append(mutantPairs)



print (classes)