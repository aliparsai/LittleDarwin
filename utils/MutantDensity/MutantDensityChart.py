import fnmatch
import os
import sys

from pygments import highlight
from pygments.lexers.jvm import JavaLexer
from pygments.formatters.html import HtmlFormatter


class DensityFormatter(HtmlFormatter):
    """Overriding formatter to highlight more than one kind of lines"""

    def __init__(self, **kwargs):
        super(DensityFormatter, self).__init__(**kwargs)
        # a list of [ (highlight_colour, [lines]) ]
        self.highlight_groups = kwargs.get('highlight_groups', [])

    def wrap(self, source, outfile):
        return self._wrap_code(source)

    # generator: returns 0, html if it's not a source line; 1, line if it is
    def _wrap_code(self, source):
        _prefix = ''
        if self.cssclass is not None:
            _prefix += '<div class="highlight">'
        if self.filename is not None:
            _prefix += '<span class="filename">{}</span>'.format(self.filename)
        yield 0, _prefix + '<pre>'

        for count, _t in enumerate(source):
            i, t = _t
            if i == 1:
                # it's a line of formatted code
                for highlight_group in self.highlight_groups:
                    col, lines = highlight_group
                    # count starts from 0...
                    if (count + 1) in lines:
                        # it's a highlighted line - set the colour
                        _row = '<span style="background-color:{}">{}</span>'.format(col, t)
                        t = _row
            yield i, t

        # close open things
        _postfix = ''
        if self.cssclass is not None:
            _postfix += '</div>'
        yield 0, '</pre>' + _postfix


def highlightCode(javaCode, lineGroups):
    """
    highlight_groups = [
        (HIGHLIGHT_COLOR, hl_lines),
        (DEPRECATED_COLOR, deprecated_lines),

    """

    javaLexer = JavaLexer()
    formatter = DensityFormatter(linenos='inline', highlight_groups=lineGroups)

    return highlight(javaCode, javaLexer, formatter)


def calculateColorList(minVal, maxVal):
    distance = maxVal - minVal + 1
    colorList = list()

    for i in range(0, 255, (256 // (distance - 1))):
        hexVal = str(hex(i)[2:])
        if len(hexVal) == 1:
            hexVal = '0' + hexVal
        colorList.append("#ff" + hexVal + hexVal)

    colorList.append("#ffffff")
    colorList.reverse()

    return colorList


def calculateLineGroups(densityFile, maxLines):
    with open(densityFile, mode='r') as densityFileHandle:
        densityDict = dict()
        lineList = list()
        sumOfDensity = 0
        for line in densityFileHandle:
            lineNumber, density = [int(x) for x in line.split(',')]
            lineList.append(lineNumber)
            sumOfDensity += density
            if density in densityDict.keys():
                densityDict[density].append(lineNumber)
            else:
                densityDict[density] = [lineNumber]

    densityDict[0] = list()
    for lineNumber in range(1, maxLines):
        if lineNumber not in lineList:
            densityDict[0].append(lineNumber)

    colorList = calculateColorList(0, max(densityDict.keys()))
    highlightGroups = list()

    for key in densityDict.keys():
        highlightGroups.append((colorList[key], densityDict[key]))

    return highlightGroups, sumOfDensity


def highlightFile(fileDirPath):
    filePath = os.path.join(fileDirPath, "original.java")
    densityFile = os.path.join(fileDirPath, "density.csv")
    maxLines = sum(1 for line in open(filePath, mode='r'))
    highlightGroups, sumOfDensity = calculateLineGroups(densityFile, maxLines)
    averageDensity = sumOfDensity / maxLines

    outputFile = os.path.join(fileDirPath, "original.html")
    with open(filePath, 'r') as filePathHandle:
        fileContent = filePathHandle.read()

    with open(outputFile, 'w') as outputFileHandle:
        outputFileHandle.write("<br>Average Density: %.2f<br>" % averageDensity)
        outputFileHandle.write(highlightCode(fileContent, highlightGroups))

    return averageDensity


def findFiles(dirPath):
    dirList = list()
    for root, dirnames, filenames in os.walk(dirPath):
        for filename in fnmatch.filter(filenames, "original.java"):
            dirList.append(root)

    return dirList


if __name__ == '__main__':

    if len(sys.argv) == 1:
        print("Usage: \nMutantDensityChart [path to LittleDarwin results]\n\n")
    else:
        averageDensityDict = dict()
        resultsPath = sys.argv[1]
        for dirPath in findFiles(resultsPath):
            relativePath = os.path.relpath(dirPath, resultsPath)
            averageDensityDict[relativePath] = highlightFile(dirPath)

        with open(os.path.join(resultsPath, "densityreport.csv"), 'w') as densityReportHandle:
            for key in averageDensityDict.keys():
                densityReportHandle.write(key + ',' + str(averageDensityDict[key]) + '\n')

