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


class MutantSubsumptionGraph(object):
    def __init__(self):
        self.nodes = list()
        self.edges = dict()

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

