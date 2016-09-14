from FindSubsumingRelation import Mutant, MutantSet
import itertools


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






