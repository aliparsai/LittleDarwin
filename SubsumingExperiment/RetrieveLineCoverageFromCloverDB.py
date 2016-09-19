import os
from subprocess import PIPE, Popen
from py4j.java_gateway import JavaGateway
import atexit

class CloverDBParser(object):
    serverStatus = False
    serverProcess = None

    def __init__(self, dbFile=None, jarFile=None):
        self.cloverDB = dbFile
        self.javaCloverDBHandler = jarFile
        self.server = None
        self.opened = False
        self.gateway = JavaGateway()

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

    def jarWrapperNonBlocking(self, args):
        assert isinstance(args, list)
        stringArgs = ['java', '-jar']
        stringArgs.extend([str(x) for x in args])
        process = Popen(stringArgs)
        return process

    def getResultsFromServer(self, filePath, lineNumber):
        assert os.path.exists(self.cloverDB)
        assert isinstance(lineNumber, int)
        assert isinstance(filePath, str)

        if not CloverDBParser.serverStatus:
            CloverDBParser.serverProcess = self.jarWrapperNonBlocking([self.javaCloverDBHandler, "--server"])
            CloverDBParser.serverStatus = True


        filePathCorrected = "".join(filePath.split('java/', 1))

        if self.server is None:
            self.server = self.gateway.entry_point.getInstance()

        if not self.opened:
            self.server.openDB(os.path.abspath(self.cloverDB))
            self.opened = True

        return self.server.retrieveResults(filePathCorrected, lineNumber)

    def getResults(self, filePath, lineNumber):
        assert os.path.exists(self.cloverDB)
        assert os.path.exists(self.javaCloverDBHandler)
        assert isinstance(lineNumber, int)
        assert isinstance(filePath, str)
        filePathCorrected = "".join(filePath.split('java/', 1))
        result = self.jarWrapper([self.javaCloverDBHandler, self.cloverDB, filePathCorrected, lineNumber])
        return result

    def findCoverage(self, filePath, lineNumber, clientMode=False):
        if not clientMode:
            rawResult = self.getResults(filePath, lineNumber)
        else:
            rawResult = self.getResultsFromServer(filePath, lineNumber)

        try:
            result = int(rawResult[0])
        except:
            result = -1

        return result, set(rawResult[1:])


def termination():
    if CloverDBParser.serverProcess is not None:
        CloverDBParser.serverProcess.terminate()

atexit.register(termination)
