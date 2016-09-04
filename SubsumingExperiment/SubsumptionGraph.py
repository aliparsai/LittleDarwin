from FindSubsumingRelation import Mutant, MutantSet
import itertools

class MutantSubsumptionGraphNode(object):
    newID = itertools.count().next
    def __init__(self):
        self.id = MutantSubsumptionGraphNode.newID()
        self.mutants = set()

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
    def __init__(self):
        self.nodes = list()
        self.edges = list()

    def addMutant(self, mutant):
        assert isinstance(mutant, Mutant)
        addCounter = 0

        for node in self.nodes:
            assert isinstance(node, MutantSubsumptionGraphNode)
            addCounter += node.addMutant(mutant)

        assert addCounter <= 1
        if addCounter == 0:
            newNode = MutantSubsumptionGraphNode()
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



