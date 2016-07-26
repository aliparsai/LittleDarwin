import os
from subprocess import PIPE, Popen


class CloverDBParser(object):
    def __init__(self, dbFile=None, jarFile=None):
        self.cloverDB = dbFile
        self.javaCloverDBHandler = jarFile

    def jarWrapper(self, args):
        assert isinstance(args, list)
        stringArgs = ['java', '-jar']
        stringArgs.extend([str(x) for x in args])
        process = Popen(stringArgs, stdout=PIPE, stderr=PIPE)
        returnResults = list()
        while process.poll() is None:
            line = process.stdout.readline()
            if line != '' and line.endswith('\n'):
                returnResults.append(line[:-1])
        stdout, stderr = process.communicate()
        returnResults += stdout.split('\n')
        if stderr != '':
            returnResults += stderr.split('\n')
        returnResults.remove('')
        return returnResults

    def getResults(self, filePath, lineNumber):
        assert os.path.exists(self.cloverDB)
        assert os.path.exists(self.javaCloverDBHandler)
        assert isinstance(lineNumber, int)
        result = self.jarWrapper([self.javaCloverDBHandler, self.cloverDB, filePath, lineNumber])
        return result

    def findTestCases(self, filePath, lineNumber):
        return self.getResults(filePath, lineNumber)[1:]

    def findCoverage(self, filePath, lineNumber):
        assert isinstance(filePath, str)
        filePathCorrected = "".join(filePath.split('java/', 1))

        try:
            result = int(self.getResults(filePathCorrected, lineNumber)[0])
        except:
            result = -1

        return result


