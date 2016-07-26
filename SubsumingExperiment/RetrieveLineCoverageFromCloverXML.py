import xml.etree.ElementTree

class CloverXMLReportParser(object):
    def __init__(self, reportFile = None):
        self.reportFile = reportFile
        self.xmlTree = None

        if self.reportFile is not None:
            self.parse()

    def parse(self):
        self.xmlTree = xml.etree.ElementTree.parse(self.reportFile).getroot()
        assert isinstance(self.xmlTree, xml.etree.ElementTree.Element)

    def findMatchingFile(self, filePath):
        assert filePath is not None
        assert isinstance(self.xmlTree, xml.etree.ElementTree.Element)

        for fileElement in self.xmlTree.iter(tag="file"):
            assert isinstance(fileElement, xml.etree.ElementTree.Element)
            if filePath in fileElement.get("path"):
                return fileElement

    def findCoverageForLine(self, fileElement, lineNumber):
        assert isinstance(fileElement, xml.etree.ElementTree.Element)
        assert isinstance(lineNumber, int)

        latest = -1
        for lineElement in fileElement.iter("line"):
            assert isinstance(lineElement, xml.etree.ElementTree.Element)
            if int(lineElement.get("num")) <= lineNumber:
                if lineElement.get("count") is not None:
                    latest = int(lineElement.get("count"))
            else:
                break
        return latest

    def findCoverage(self, filePath, lineNumber):
        return self.findCoverageForLine(self.findMatchingFile(filePath), lineNumber)


#
# rp = CloverXMLReportParser("clover.xml")
# assert isinstance(rp.xmlTree, xml.etree.ElementTree.Element)
#
# print rp.findCoverage("java/com/addthis/codec/plugins/PluginMap.java", 68)





