from FindSubsumingRelation import *


def mapCorrespondingMutants(mutantSet1, mutantSet2):
    assert isinstance(mutantSet1, MutantSet)
    assert isinstance(mutantSet2, MutantSet)

    mutantMap = dict()

    for mutant1 in mutantSet1.mutants:
        for mutant2 in mutantSet1.mutants:
            if mutant1.path == mutant2.path:
                mutantMap[mutant1] = mutant2

    return mutantMap

def printResultsMultiple(mutantSet1, mutantSet2):
    assert isinstance(mutantSet1, MutantSet)
    assert isinstance(mutantSet2, MutantSet)

    truePositiveSubsuming = 0
    trueNegativeSubsuming = 0
    falsePositiveSubsuming = 0
    falseNegativeSubsuming = 0

    mutantMap = mapCorrespondingMutants(mutantSet1, mutantSet2)

    for mutant in mutantSet1.mutants:
        assert isinstance(mutant, Mutant)
        if mutant.isProbablySubsuming and mutantMap[mutant].isSubsuming:
            truePositiveSubsuming += 1
        elif mutant.isProbablySubsuming and not mutantMap[mutant].isSubsuming:
            falsePositiveSubsuming += 1
        elif not mutant.isProbablySubsuming and mutantMap[mutant].isSubsuming:
            falseNegativeSubsuming += 1
        elif not mutant.isProbablySubsuming and not mutantMap[mutant].isSubsuming:
            trueNegativeSubsuming += 1

    totalMutants = len(mutantSet.mutants)
    assert totalMutants == truePositiveSubsuming + falsePositiveSubsuming + trueNegativeSubsuming + falseNegativeSubsuming

    precisionSubsuming = 100 * truePositiveSubsuming / float(truePositiveSubsuming + falsePositiveSubsuming)
    recallSubsuming = 100 * truePositiveSubsuming / float(truePositiveSubsuming + falseNegativeSubsuming)
    accuracySubsuming = 100 * (truePositiveSubsuming + trueNegativeSubsuming) / float(totalMutants)

    print "Subsuming Prediction:", len(
        mutantSet.mutants), "\nTP:", truePositiveSubsuming, " FP:", falsePositiveSubsuming, "\nFN:", falseNegativeSubsuming, "TN:", trueNegativeSubsuming
    print "----------------------------\nPrecision: %.2f" % precisionSubsuming, "\nRecall: %.2f" % recallSubsuming, "\nAccuracy: %.2f" % accuracySubsuming, "\n****************************"


mutantSetOld = MutantSet(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[7])
mutantSetNew = MutantSet(sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])

mutantSetOld.retrieveMutants()
mutantSetOld.assignStatus()
mutantSetOld.predictStatus(1.0)
mutantSetNew.retrieveMutants()
mutantSetNew.assignStatus()
mutantSetNew.predictStatus(1.0)

printResultsMultiple(mutantSetOld, mutantSetNew)
