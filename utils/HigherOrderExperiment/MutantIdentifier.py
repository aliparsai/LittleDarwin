import fnmatch
import sys
import os


class Mutant(object):
    def __init__(self):
        self.id = None
        self.nodes = list()
        self.status = 999     # 0 unknown, 1 survived, -1 killed, 999 unset
        self.path = None

    def __str__(self):
        return " ".join(str(x) for x in ["Mutant ", self.id, "| Path:", self.path, "| Status:", self.status, "| Nodes:", self.nodes])


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
    print("Error: FirstOrderPath Incorrect.", firstOrderPath)
    sys.exit(1)


if not os.path.isdir(secondOrderPath) or not os.path.isfile(os.path.join(secondOrderPath, "report.txt")):
    print("Error: SecondOrderPath Incorrect.", secondOrderPath)
    sys.exit(1)


firstOrderClasses = listClasses(firstOrderPath)
secondOrderClasses = listClasses(secondOrderPath)

classes = dict()

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
    classes[secondOrderClass.name] = mutantPairs


# count the anomalies

writeHandle = open(sys.argv[3], "w")

for cname, c in classes.iteritems():
    processedIDs1 = list()
    processedIDs2 = list()

    s2k = 0
    k2s = 0
    normal = 0
    hcl = getClassByName(cname, secondOrderClasses)
    fcl = getClassByName(cname, firstOrderClasses)

    assert isinstance(c, dict)

    for key, value in c.iteritems():
        #### assertions

        assert key not in processedIDs2
        assert isinstance(value, list)
        assert len(value) == len(set(value))
        for k in value:
            assert k not in processedIDs1

        processedIDs2.append(key)
        processedIDs1.extend(value)

        #### counting
        hom = hcl.findMutantByID(key)
        assert isinstance(hom, Mutant)

        foms = [fcl.findMutantByID(fid) for fid in value]

        if hom.status not in [1, -1]:
            print hom, "\n unknown status"
        assert hom.status != 0


        if hom.status == -1:
            for fom in foms:
                assert isinstance(fom, Mutant)
                assert fom.status != 0
                statusFlag = False
                if fom.status == -1:
                    statusFlag = True
                    break
            if statusFlag:
                normal += 1
            else:
                sys.stdout.write(",".join(str(x) for x in [cname, hom.id, [f.id for f in foms], "all FOMs survived, HOM killed\n"]))
                s2k += 1

        elif hom.status == 1:
            for fom in foms:
                assert isinstance(fom, Mutant)
                assert fom.status != 0
                statusFlag = False
                if fom.status == -1:
                    sys.stdout.write(",".join(str(x) for x in [cname, hom.id, [f.id for f in foms], fom.id, "FOM killed, HOM survived\n"]))
                    statusFlag = True
                    break
            if statusFlag:
                k2s += 1
            else:
                normal += 1

    writeHandle.write(",".join(str(x) for x in [cname, normal, k2s, s2k, "\n"]))

writeHandle.close()
