import os
import sys
import shelve
import random
import math
import scipy.stats.stats

#
# def weightedChoice(choices, count):
#     selectedSet = set()
#     remainingCount = count
#     remainingChoices = dict()
#
#     for i in range(0, len(choices), 1):
#         remainingChoices[i] = choices[i]
#
#     while remainingCount > 0:
#         r = random.sample(range(0, sum(remainingChoices.values())+1, 1), remainingCount)
#         r.sort(reverse=True)
#         # index = 0
#         upto = 0
#
#         for index, w in remainingChoices.iteritems():
#             if len(r) == 0:
#                 break
#             if upto + w > r[-1]:
#                 selectedSet.add(index)
#                 r.pop()
#                 remainingChoices[index] = 0
#             upto += w
#             # index += 1
#
#         remainingCount = count - len(selectedSet)
#
#     return selectedSet
#
#
# def weightedSampling(choices, size):
#     # sampleSet = set()
#     weightList = list()
#     mutantList = list()
#
#     for c_a, c_b, w in choices:
#         weightList.append(w)
#         mutantList.append((c_a, c_b))
#
#     # while len(sampleSet) < size:
#     return [mutantList[x] for x in weightedChoice(weightList, size)]
#
#     # return list(sampleSet)


class SamplingExperiment(object):
    def __init__(self, sourceDatabase, resultsDatabase):
        # self.resultsDatabase = shelve.open(resultsDatabase, "r")

        try:
            self.resultsDatabase = shelve.open(resultsDatabase, "r")
            self.mutationDatabase = shelve.open(sourceDatabase, "r")

        except Exception:
            print("Error opening databases.")
            # print Exception.message.getter()
            sys.exit(1)

        self.unitCount = len(self.mutationDatabase.keys())
        assert self.unitCount == len(self.resultsDatabase.keys())

        self.mutantCount = 0
        for key in self.mutationDatabase.keys():
            self.mutantCount += len(self.mutationDatabase[key])

    def mutantSamplerFixedSize(self, size):
        sampledDatabase = dict()
        mutantList = list()
        totalLength = 0
        lengths = list()
        maxLength = -100000

        for key in self.mutationDatabase.keys():
            totalLength += len(self.mutationDatabase[key])
            maxLength = maxLength if maxLength > len(self.mutationDatabase[key]) else len(self.mutationDatabase[key])
            # lengths.append(len(self.mutationDatabase[key]))

        #
        # for key in self.mutationDatabase.keys():
        #     thisLength = len(self.mutationDatabase[key])
        #     for mutant in self.mutationDatabase[key]:
        #         mutantList.append((key, mutant, 101 - ((thisLength * 100) / maxLength)))

        # for key in self.mutationDatabase.keys():
        # thisLength = len(self.mutationDatabase[key])
        #     for mutant in self.mutationDatabase[key]:
        #         mutantList.append((key, mutant, int(1002 - (thisLength/float(totalLength))*1000)**2))
        # #
        for key in self.mutationDatabase.keys():
            for mutant in self.mutationDatabase[key]:
                mutantList.append((key, mutant))


        selectedList = random.sample(mutantList, size)

        # selectedList = weightedSampling(mutantList, size)

        for key in self.mutationDatabase.keys():
            thisKey = list()
            for candidateKey, candidateMutant in selectedList:
                if candidateKey == key:
                    thisKey.append(os.path.basename(candidateMutant))
            thisKey.sort()

            sampledDatabase[key] = thisKey

        return sampledDatabase


    def checkResults(self, key, database):

        survivedList, killedList = self.resultsDatabase[key]
        sampledSurvivedList = list()
        sampledKilledList = list()

        for mutant in database[key]:
            if mutant in survivedList:
                sampledSurvivedList.append(mutant)
            elif mutant in killedList:
                sampledKilledList.append(mutant)

        return sampledSurvivedList, sampledKilledList

    def calculateCoverage(self, database):
        coverage = dict()
        for key in database.keys():
            survived, killed = database[key]
            # print survived, killed
            if len(survived) + len(killed) > 0:
                score = float(len(killed)) / float(len(survived) + len(killed))
            else:
                score = 0.0
            coverage[key] = score

        return coverage

    def calculateOverallCoverage(self, database):
        totalSurvived = 0
        totalKilled = 0
        for key in database.keys():
            survived, killed = database[key]
            # print survived, killed
            # if len(survived) + len(killed) > 0:

            totalSurvived += len(survived)
            totalKilled += len(killed)

            # score = float(len(killed)) / float(len(survived) + len(killed))
            # else:
            #     score = 0.0

        coverage = float(totalKilled) / float(totalSurvived + totalKilled)
        return coverage

    def experimentOnce(self, sampleSize):
        sampledDatabase = self.mutantSamplerFixedSize(sampleSize)
        resultsSampledDatabase = dict()

        for key in sampledDatabase.keys():
             survivedList, killedList = self.checkResults(key, sampledDatabase)
             resultsSampledDatabase[key] = (survivedList, killedList)

        coverageFullSet = self.calculateOverallCoverage(self.resultsDatabase)
        coverageSampledSet = self.calculateOverallCoverage(resultsSampledDatabase)

        # sampledList = list()
        # fullList = list()

        # for key in coverageFullSet.keys():
        #     fullList.append(int(coverageFullSet[key] * 1000))
        #     if key in coverageSampledSet.keys():
        #         sampledList.append(int(coverageSampledSet[key] * 1000))
        #     else:
        #         sampledList.append(0)

        # print sampledList, fullList
        # kendall_t, kendall_p = scipy.stats.stats.kendalltau(sampledList, fullList)
        # pearson_r, pearson_p = scipy.stats.stats.pearsonr(sampledList, fullList)

        return coverageSampledSet, coverageFullSet
        # pearson_r, kendall_t


if __name__ == "__main__":
    # print os.path.join(sys.argv[1], "mutationdatabase")
    exp = SamplingExperiment(os.path.join(sys.argv[1], "mutationdatabase"),
                             os.path.join(sys.argv[1], "mutationdatabase-results"))
    # pearson = list()
    # kendall = list()
    sampled = list()
    for i in range(1, 100, 1):
        sys.stdout.write(str(i) + "\r")
        sys.stdout.flush()

        # sumPearson = 0.0
        # sumKendall = 0.0
        sumSampled = 0.0
        # sumFull = 0.0
        sampleSize = int(i * exp.mutantCount / 100)
        for j in range(0, 10, 1):
            s, f = exp.experimentOnce(sampleSize)

            # if math.isnan(p):
            #     p = 0.0
            # if math.isnan(k):
            #     k = 0.0


            sumSampled += s
            # sumFull += f

            # sumKendall += k
        # assert sumFull/10 == f
        # pearson.append(int(sumPearson * 1000))
        # kendall.append(int(sumKendall * 1000))

        sampled.append(int(sumSampled*100))

    with open(sys.argv[2], 'w') as output:
        # assert len(pearson) == len(kendall)
        for counter in range(0, len(sampled), 1):
            output.write(str(sampled[counter]) + "\n")
