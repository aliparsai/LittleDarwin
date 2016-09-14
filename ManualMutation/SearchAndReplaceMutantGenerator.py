from ManualMutation import *
import tempfile

class SearchAndReplaceMutation(ManualMutation):
    def __init__(self, sourcePath = None):
        ManualMutation.__init__(self, sourcePath, None)
        self.tmpFilePaths = list()

    def initialize(self):
        assert os.path.isdir(self.sourcePath)

        sourceFilePaths = self.listFiles(self.sourcePath)
        for sourceFilePath in sourceFilePaths:
            tmpRelativePath = os.path.relpath(sourceFilePath, self.sourcePath)
            tmpSourceFileObj = SourceFile(tmpRelativePath, sourceFilePath)
            tmpSourceFileObj.readContents()
            self.sourceFiles.append(tmpSourceFileObj)
            sys.stdout.write(str(len(self.sourceFiles)) + " source files found.   \r")

        sys.stdout.write("\n")

    def mutateSource(self, sourceFile, searchTerm=None, replacement=""):
        assert isinstance(searchTerm, str)
        assert isinstance(sourceFile, SourceFile)
        assert isinstance(replacement, str)

        results = list()
        tokens = sourceFile.contents.split(searchTerm)

        for i in range(0, len(tokens)-1):
            tmpList = list()

            for j in range(0, len(tokens)):
                tmpList.append(tokens[j])

                if i == j:
                    tmpList.append(replacement + " /* <- mutated from \'" + searchTerm + "\' */ ")
                elif i != j and j != len(tokens) - 1:
                    tmpList.append(searchTerm)

            results.append("".join(tmpList))

        return results

    def createTempMutantFile(self, contents=""):
        assert isinstance(contents, str)

        tmpFileHandle, tmpFilePath = tempfile.mkstemp(suffix=".java", prefix="mutant_", text=True)
        self.tmpFilePaths.append(tmpFilePath)
        os.write(tmpFileHandle, contents)
        tmpMutant = MutantFile(None, tmpFilePath)

        return tmpMutant

    def mutateAllSourceFiles(self, searchTerm, replacement):
        for srcFile in self.sourceFiles:
            assert isinstance(srcFile, SourceFile)

            mutatedCodeList = self.mutateSource(srcFile, searchTerm, replacement)
            for mutatedCode in mutatedCodeList:
                cMutant = self.createTempMutantFile(mutatedCode)
                self.mutantFiles.append(cMutant)
                srcFile.associatedMutantFiles.append(cMutant)


if __name__ == "__main__":
    srcPath = sys.argv[1]
    search = sys.argv[2]
    replace = sys.argv[3]

    assert os.path.isdir(srcPath)

    mm = SearchAndReplaceMutation(srcPath)

    mm.initialize()
    mm.mutateAllSourceFiles(search, replace)
    mm.createMutationStructure()

    for tmpfile in mm.tmpFilePaths:
        os.remove(tmpfile)




