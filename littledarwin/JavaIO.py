import fnmatch
import io
import os
import shutil

class JavaIO(object):
    """

    """
    def __init__(self, verbose=False):
        self.verbose = False
        self.sourceDirectory = None
        self.targetDirectory = None
        self.fileList = list()

    def filterFiles(self, mode="blacklist", filterList=None):
        """

        :param mode:
        :type mode:
        :param filterList:
        :type filterList:
        :return:
        :rtype:
        """
        if filterList is None:
            return

        assert isinstance(filterList, list)
        assert mode == "blacklist" or mode == "whitelist"

        alteredList = list()
        packageList = list()
        cuList = list()

        for statement in filterList:
            if '\\' in statement or '/' in statement:
                cuList.append(statement)
            else:
                packageList.append(statement)

        for packageName in packageList:
            if str(packageName).strip() == "":
                continue

            # we need to do this so that we avoid partial matching

            dirList = list()
            dirList.append("")
            dirList.extend(packageName.strip().split("."))
            dirList.append("")
            dirName = os.sep.join(dirList)

            alteredList.extend([x for x in self.fileList if dirName in os.sep.join(["", x, ""])])

        for cuName in cuList:
            alteredList.extend([x for x in self.fileList if cuName in x])

        if mode == "whitelist":
            self.fileList = list(set(alteredList))
        elif mode == "blacklist":
            self.fileList = list(set(self.fileList) - set(alteredList))

    def listFiles(self, targetPath=None, buildPath=None, filterList=None, filterType="blacklist", desiredType="*.java"):
        """

        :param targetPath:
        :type targetPath:
        :param buildPath:
        :type buildPath:
        :param filterList:
        :type filterList:
        :param filterType:
        :type filterType:
        :param desiredType:
        :type desiredType:
        """
        # print targetPath, desiredType
        self.sourceDirectory = targetPath
        self.targetDirectory = os.path.abspath(os.path.join(buildPath, "LittleDarwinResults"))

        for root, dirnames, filenames in os.walk(self.sourceDirectory):
            for filename in fnmatch.filter(filenames, desiredType):
                self.fileList.append(os.path.join(root, filename))

        self.filterFiles(mode=filterType, filterList=filterList)

        if not os.path.exists(self.targetDirectory):
            os.makedirs(self.targetDirectory)

    def getFileContent(self, filePath=None):
        """

        :param filePath:
        :type filePath:
        :return:
        :rtype:
        """
        with io.open(filePath, mode='r', errors='replace') as contentFile:
            file_data = contentFile.read()
        normalizedData = str(file_data)
        return normalizedData

    def generateNewFile(self, originalFile=None, fileData=None, mutantsPerLine=None, densityReport=None):
        """

        :param densityReport:
        :type densityReport:
        :param originalFile:
        :type originalFile:
        :param fileData:
        :type fileData:
        :param mutantsPerLine:
        :type mutantsPerLine:
        :return:
        :rtype:
        """
        originalFileRoot, originalFileName = os.path.split(originalFile)

        targetDir = os.path.join(self.targetDirectory, os.path.relpath(originalFileRoot, self.sourceDirectory),
                                 originalFileName)

        if not os.path.exists(targetDir):
            os.makedirs(targetDir)
        if not os.path.isfile(os.path.join(targetDir, "original.java")):
            shutil.copyfile(originalFile, os.path.join(targetDir, "original.java"))

        if mutantsPerLine is not None and densityReport is not None:
            densityCSVFile = os.path.abspath(os.path.join(targetDir, "density.csv"))
            densityReportFile = os.path.abspath(os.path.join(targetDir, "original.html"))

            if not os.path.isfile(densityCSVFile) or not os.path.isfile(densityReportFile):
                with open(densityCSVFile, 'w') as densityFileHandle:
                    for key in sorted(mutantsPerLine.keys()):
                        densityFileHandle.write(str(key) + ',' + str(mutantsPerLine[key]) + '\n')

                with open(densityReportFile, 'w') as densityFileHandle:
                    densityFileHandle.write(densityReport)


        counter = 1
        while os.path.isfile(os.path.join(targetDir, str(counter) + ".java")):
            counter += 1

        targetFile = os.path.abspath(os.path.join(targetDir, str(counter) + ".java"))
        with open(targetFile, 'w') as contentFile:
            contentFile.write(fileData)

        if self.verbose:
            print("--> generated file: ", targetFile)
        return os.path.relpath(targetFile, self.targetDirectory)
