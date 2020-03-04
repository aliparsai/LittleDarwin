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


class MutantDensityGenerator(object):
    """
    Generates visual report on mutant density
    """
    def __init__(self):
        pass

    def highlightCode(self, javaCode, lineGroups):
        """
        Generates HTML highlights
        """
        javaLexer = JavaLexer()
        formatter = DensityFormatter(linenos='inline', highlight_groups=lineGroups)

        return highlight(javaCode, javaLexer, formatter)

    def calculateColorList(self, minVal, maxVal):
        """

        :param minVal:
        :type minVal:
        :param maxVal:
        :type maxVal:
        :return:
        :rtype:
        """
        distance = maxVal - minVal + 1
        colorList = list()

        if distance > 1:
            for i in range(0, 255, (256 // (distance - 1))):
                hexVal = str(hex(i)[2:])
                if len(hexVal) == 1:
                    hexVal = '0' + hexVal
                colorList.append("#ff" + hexVal + hexVal)

        colorList.append("#ffffff")
        colorList.reverse()

        return colorList

    def calculateLineGroups(self, densityDict: dict, maxLines: int) -> (list, int):
        """

        :param densityDict:
        :type densityDict:
        :param maxLines:
        :type maxLines:
        :return:
        :rtype:
        """
        sumOfDensity = 0
        reverseDensityDict = dict()
        for lineNumber in densityDict.keys():
            sumOfDensity += densityDict[lineNumber]
            reverseDensityDict[densityDict[lineNumber]] = reverseDensityDict.get(densityDict[lineNumber], list()) + [ lineNumber ]

        reverseDensityDict[0] = list()
        for lineNumber in range(1, maxLines):
            if lineNumber not in densityDict.keys():
                reverseDensityDict[0].append(lineNumber)

        colorList = self.calculateColorList(0, max(reverseDensityDict.keys()))
        highlightGroups = list()
        for density in reverseDensityDict.keys():
            highlightGroups.append((colorList[density], reverseDensityDict[density]))

        return highlightGroups, sumOfDensity

    def highlightFile(self, fileContent: str, densityDict: dict) -> (str, float):
        """

        :param fileContent:
        :type fileContent:
        :param densityDict:
        :type densityDict:
        :return:
        :rtype:
        """
        maxLines = sum(1 for line in fileContent.splitlines())
        highlightGroups, sumOfDensity = self.calculateLineGroups(densityDict, maxLines)
        averageDensity = sumOfDensity / maxLines
        highlightedHTML = "<br>Average Density: %.2f<br>" % averageDensity
        highlightedHTML += self.highlightCode(fileContent, highlightGroups)

        return highlightedHTML, averageDensity
