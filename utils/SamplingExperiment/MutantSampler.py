from optparse import OptionParser
import random
import shelve
import sys

__author__ = 'perham'

def countFunction(num):
    assert isinstance(num, int)
    assert num >= 0
    if num < 10:
        return int(num)
    elif num < 30:
        return max(int(num * 0.8), 10)
    elif num < 60:
        return max(int(num * 0.5), 24)
    elif num < 100:
        return max(int(num * 0.4), 30)
    elif num < 200:
        return max(int(num * 0.3), 40)
    elif num < 500:
        return max(int(num * 0.2), 60)
    else:
        return max(int(num * 0.1), 100)


def MutantSampler(sourceDatabase, targetDatabase):
    try:
        mutationDatabase = shelve.open(sourceDatabase, "r")
        sampledDatabase = shelve.open(targetDatabase, "c")

    except Exception:
        print("Error opening databases.")
        sys.exit(1)


    databaseLength = len(mutationDatabase.keys())
    currentKey = 0
    totalSelected = 0
    totalMutants = 0

    for key in mutationDatabase.keys():
        currentKey += 1
        sourceMutants = mutationDatabase[key]
        sampleSize = countFunction(len(sourceMutants))

        totalMutants += len(sourceMutants)
        totalSelected += sampleSize

        sampledDatabase[key] = random.sample(sourceMutants, sampleSize)

        print("current key:" + key + " ** number of mutants: " + str(len(sourceMutants)) + " | selected sample: " + str(sampleSize))

    print("total number of mutants: " + str(totalMutants) + " ** total selected: " + str(totalSelected))



if __name__ == "__main__":
    optionParser = OptionParser()

    optionParser.add_option("-s", "--source", action="store", dest="sourcedb", default="***dummy***", help="Source database")
    optionParser.add_option("-t", "--target", action="store", dest="targetdb", default="***dummy***", help="Target database")
    # optionParser.add_option("-f", "--fixed-size", action="store", dest="fixedsize", default="***dummy***", help="Target database")

    (options, args) = optionParser.parse_args()

    if options.sourcedb == "***dummy***" or options.targetdb == "***dummy***":
        print("Needs both input arguments")
        sys.exit(1)

    MutantSampler(options.sourcedb, options.targetdb)



