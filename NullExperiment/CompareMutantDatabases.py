import os
import sys
import shelve
import random
import math
import scipy.stats.stats

class MutantResults(object):
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

    def calculateCoverageForClass(self, c):

        if not self.resultsDatabase.has_key(c):
            return None

        survivedList, killedList = self.resultsDatabase[c]
        if len(survivedList) + len(killedList) > 0:
            score = float(len(killedList)) / float(len(survivedList) + len(killedList))
        else:
            score = None

        return score

    def calculateCoverageForType(self, t):
        pass


if __name__ == "__main__":
    pass
