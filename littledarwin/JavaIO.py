import fnmatch
import io
import os
import shutil
from typing import Dict, List


class JavaIO(object):
    """
    This class handles all the file I/O operations for LittleDarwin, such as
    finding Java files, reading their content, and writing the mutated files
    to disk.
    """

    def __init__(self, verbose=False):
        """
        Initializes the JavaIO object.

        :param verbose: Whether to print verbose output.
        :type verbose: bool
        """
        self.verbose = False
        self.sourceDirectory = None
        self.targetDirectory = None
        self.fileList = list()

    def filterFiles(self, mode="blacklist", filterList=None):
        """
        Filters the list of files based on a whitelist or blacklist.

        :param mode: The filter mode, either "whitelist" or "blacklist".
        :type mode: str
        :param filterList: A list of package names or file paths to filter by.
        :type filterList: list
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
        Lists all the files in a directory that match a given type, and
        optionally filters them.

        :param targetPath: The path to the source files.
        :type targetPath: str
        :param buildPath: The path to the build directory.
        :type buildPath: str
        :param filterList: A list of package names or file paths to filter by.
        :type filterList: list
        :param filterType: The filter mode, either "whitelist" or "blacklist".
        :type filterType: str
        :param desiredType: The type of files to list (e.g., "``*.java``").
        :type desiredType: str
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
        Reads the content of a file and returns it as a string.

        :param filePath: The path to the file.
        :type filePath: str
        :return: The content of the file.
        :rtype: str
        """
        with io.open(filePath, mode='r', errors='replace') as contentFile:
            file_data = contentFile.read()
        normalizedData = str(file_data)
        return normalizedData

    def getAggregateComplexityReport(self, mutantDensityPerMethod: Dict[str, int],
                                     cyclomaticComplexityPerMethod: Dict[str, int],
                                     linesOfCodePerMethod: Dict[str, int]) -> Dict[str, List[int]]:
        """
        Aggregates complexity metrics for each method in a class.

        :param mutantDensityPerMethod: A dictionary mapping method names to the
                                       number of mutants in that method.
        :type mutantDensityPerMethod: dict
        :param cyclomaticComplexityPerMethod: A dictionary mapping method names
                                              to their cyclomatic complexity.
        :type cyclomaticComplexityPerMethod: dict
        :param linesOfCodePerMethod: A dictionary mapping method names to their
                                     lines of code.
        :type linesOfCodePerMethod: dict
        :return: A dictionary mapping method names to a list containing the
                 mutant density, cyclomatic complexity, and lines of code.
        :rtype: dict
        """
        aggregateReport = dict()
        methodList = set(mutantDensityPerMethod.keys())
        methodList.update(cyclomaticComplexityPerMethod.keys())
        methodList.update(linesOfCodePerMethod.keys())

        for method in methodList:
            aggregateReport[method] = [mutantDensityPerMethod.get(method, 0),
                                       cyclomaticComplexityPerMethod.get(method, 1),
                                       linesOfCodePerMethod.get(method, 0)]

        return aggregateReport

    def generateNewFile(self, originalFile=None, fileData=None, mutantsPerLine=None, densityReport=None, aggregateComplexity=None):
        """
        Generates a new file containing a mutant.

        This function creates a new directory for the mutated file, copies the
        original file to that directory, and then writes the mutated code to a
        new file in that directory. It also writes out a number of reports
        about the mutation.

        :param originalFile: The path to the original file.
        :type originalFile: str
        :param fileData: The content of the mutated file.
        :type fileData: str
        :param mutantsPerLine: A dictionary mapping line numbers to the number
                               of mutants on that line.
        :type mutantsPerLine: dict
        :param densityReport: The HTML report of the mutant density.
        :type densityReport: str
        :param aggregateComplexity: A dictionary containing the aggregate
                                    complexity report for the class.
        :type aggregateComplexity: dict
        :return: The relative path to the new file.
        :rtype: str
        """
        originalFileRoot, originalFileName = os.path.split(originalFile)

        targetDir = os.path.join(self.targetDirectory, os.path.relpath(originalFileRoot, self.sourceDirectory),
                                 originalFileName)

        if not os.path.exists(targetDir):
            os.makedirs(targetDir)
        if not os.path.isfile(os.path.join(targetDir, "original.java")):
            shutil.copyfile(originalFile, os.path.join(targetDir, "original.java"))

        if mutantsPerLine is not None and densityReport is not None and aggregateComplexity is not None:
            densityPerLineCSVFile = os.path.abspath(os.path.join(targetDir, "MutantDensityPerLine.csv"))
            complexityPerMethodCSVFile = os.path.abspath(os.path.join(targetDir, "ComplexityPerMethod.csv"))
            densityReportFile = os.path.abspath(os.path.join(targetDir, "aggregate.html"))

            if not os.path.isfile(complexityPerMethodCSVFile) or not os.path.isfile(
                    densityPerLineCSVFile) or not os.path.isfile(densityReportFile):
                with open(densityPerLineCSVFile, 'w', encoding="utf-8") as densityFileHandle:
                    for key in sorted(mutantsPerLine.keys()):
                        densityFileHandle.write(str(key) + ',' + str(mutantsPerLine[key]) + '\n')

                with open(complexityPerMethodCSVFile, 'w', encoding="utf-8") as densityFileHandle:
                    for key in sorted(aggregateComplexity.keys()):
                        line = [str(key)]
                        line.extend([str(x) for x in aggregateComplexity[key]])
                        densityFileHandle.write(";".join(line) + '\n')

                with open(densityReportFile, 'w', encoding="utf-8") as densityFileHandle:
                    densityFileHandle.write(densityReport)

        counter = 1
        while os.path.isfile(os.path.join(targetDir, str(counter) + ".java")):
            counter += 1

        targetFile = os.path.abspath(os.path.join(targetDir, str(counter) + ".java"))
        with open(targetFile, 'w', encoding="utf-8") as contentFile:
            contentFile.write(fileData)

        if self.verbose:
            print("--> generated file: ", targetFile)
        return os.path.relpath(targetFile, self.targetDirectory)
