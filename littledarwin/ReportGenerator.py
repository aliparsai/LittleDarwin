import os
import shelve


class ReportGenerator(object):
    """

    """
    def __init__(self, littleDarwinVersion=None):
        self.database = None
        self.ldVersion = littleDarwinVersion

    def initiateDatabase(self, databasePath):
        """

        :param databasePath:
        :type databasePath:
        """
        self.database = shelve.open(databasePath, "c")

    def generateHTMLFinalReport(self, resultData, reportPath):
        """

        :param resultData:
        :type resultData:
        :param reportPath:
        :type reportPath:
        :return:
        :rtype:
        """
        reportBeginning = """<!DOCTYPE html><html><head><title>LittleDarwin Mutation Coverage Report</title>
             <style type='text/css'> body { font-family: "Carlito", "Calibri", "Helvetica Neue", sans-serif; } 
             table { border-collapse: collapse; } th, td { text-align: left; padding: 1em; }
             th { background-color: #f0f0f0; color: black; } tr:hover { background-color: #b2daf5; } 
             a:link, a:visited { color: black; text-decoration: none; display: inline-block; } 
             a:hover, a:active { font-weight: bold; } .coverage_bar { display: inline-block; border-radius: 0.3em; 
             height: 1.1em; width: 9em; background: #ff8482; margin: 0 5px; vertical-align: middle; 
             border: 1px solid #888; position: relative } .coverage_complete { display: inline-block; 
             border-radius: 0.3em; height: 100%; background: #acff8b; float: left } 
             .coverage_legend { position: absolute; height: 100%; width: 100%; left: 0; top: 0; text-align: center }
             </style></head><body><h1>LittleDarwin Mutation Coverage Report</h1>
             <h2>Project Summary</h2><table><thead><tr><th>Number of Files</th>
             <th colspan=2>Mutation Coverage</th></tr> </thead> <tbody>"""

        reportMiddle = """</tbody></table><h2>Breakdown by File</h2><table><thead><tr><th>Name</th>
                          <th colspan=2 >Mutation Coverage</th></tr></thead><tbody>"""

        reportEnd = """</tbody></table><footer><p style="font-size: small">Report generated by LittleDarwin {} </p>
                       </footer></body></html>""".format(self.ldVersion)

        totalMutantCount = 0
        survivedMutantCount = 0
        breakdownFile = list()

        for mutationResult in resultData:
            survivedMutantCount += mutationResult[1]
            totalMutantCount += mutationResult[2]
            breakdownFile.append("<tr><td><a href=\"" + os.path.relpath(
                os.path.join(os.path.dirname(reportPath), mutationResult[0], "results.html"),
                os.path.dirname(reportPath)) + "\" >" + os.path.relpath(
                os.path.join(os.path.dirname(reportPath), mutationResult[0]),
                os.path.dirname(reportPath)) + "</a></td> <td> " +
                                 ("{:3.1f}%".format(100 - (mutationResult[1] / float(mutationResult[2]) * 100)))
                         + " </td> <td> <div class=\"coverage_bar\"><div class=\"coverage_complete\" style=\"width:" +
                         ("%d" % (100 - (mutationResult[1] / float(mutationResult[2]) * 100)))
                         + "%\"></div><div class=\"coverage_legend\">" + str(mutationResult[2] - mutationResult[1])
                         + "/" + str(mutationResult[2]) + "</div></div></td></tr>")

        killedMutantCount = totalMutantCount - survivedMutantCount

        projectOverallStats = "<tr><td>" + str(len(resultData)) + " </td> <td> " + ("%3.1f" % (float(
                              killedMutantCount) / totalMutantCount * 100)) \
                              + " </td> <td> <div class=\"coverage_bar\"><div class=\"coverage_complete\" style=\"width:"\
                              + ("%d" % (float(killedMutantCount) / totalMutantCount * 100)) \
                              + "%\"></div><div class=\"coverage_legend\">" + str(killedMutantCount) + "/" \
                              + str(totalMutantCount) + "</div></div></td></tr>"

        reportOutput = list()
        reportOutput.extend([reportBeginning, projectOverallStats, reportMiddle])
        reportOutput.extend(breakdownFile)
        reportOutput.append(reportEnd)

        return '\n'.join(reportOutput)

    def generateHTMLReportPerFile(self, filePath, reportPath, survived, killed):
        """

        :param filePath:
        :type filePath:
        :param reportPath:
        :type reportPath:
        :param survived:
        :type survived:
        :param killed:
        :type killed:
        :return:
        :rtype:
        """
        def xstr(inputVar):
            """

            :param inputVar:
            :type inputVar:
            :return:
            :rtype:
            """
            if inputVar is None:
                return ''
            else:
                return str(inputVar)

        self.database[filePath] = (survived, killed)

        reportBeginning = """<!DOCTYPE html><html><head><title>LittleDarwin Mutation Coverage Report</title>
             <style type='text/css'> body { font-family: "Carlito", "Calibri", "Helvetica Neue", sans-serif; } 
             table { border-collapse: collapse; } th, td { text-align: left; padding: 1em; }
             th { background-color: #f0f0f0; color: black; } tr:hover { background-color: #b2daf5; } 
             a:link, a:visited { color: black; text-decoration: none; display: inline-block; } 
             a:hover, a:active { font-weight: bold; } .coverage_bar { display: inline-block; border-radius: 0.3em; 
             height: 1.1em; width: 9em; background: #ff8482; margin: 0 5px; vertical-align: middle; 
             border: 1px solid #888; position: relative } .coverage_complete { display: inline-block; 
             border-radius: 0.3em; height: 100%; background: #acff8b; float: left } 
             .coverage_legend { position: absolute; height: 100%; width: 100%; left: 0; top: 0; text-align: center }
             </style></head><body><h1>LittleDarwin Mutation Coverage Report</h1><h2>File Summary</h2><table><thead><tr>
             <th>Number of Mutants</th><th>Mutation Coverage</th></tr></thead><tbody>"""

        reportMiddle = """<tr><td colspan=2 style="text-align:center"><a href="original.html">Aggregate Report</a></td>
                          </tr></tbody></table><h2>Detailed List</h2><br><table><thead><tr><th>Survived Mutant</th>
                          <th>Build Output</th><th>Killed Mutant</th><th>Build Output</th></tr></thead><tbody>"""

        reportEnd = """</tbody></table><footer><p style="font-size: small">Report generated by LittleDarwin %s </p>
                               </footer></body></html>""" % self.ldVersion

        output = list()
        joinedList = list()

        if len(survived) > len(killed):
            maxIndex = len(survived)
        else:
            maxIndex = len(killed)

        assert isinstance(survived, list)
        assert isinstance(killed, list)

        for i in range(0, maxIndex):
            try:
                survivedItem = survived[i]
            except IndexError as e:
                survivedItem = None

            try:
                killedItem = killed[i]
            except IndexError as e:
                killedItem = None

            joinedList.append([os.path.relpath(os.path.join(os.path.dirname(reportPath), survivedItem),
                                               os.path.dirname(reportPath)) if survivedItem is not None else None,
                               survivedItem, os.path.relpath(
                    os.path.join(os.path.dirname(reportPath), os.path.splitext(survivedItem)[0] + ".txt"),
                    os.path.dirname(reportPath)) if survivedItem is not None else None,
                               os.path.splitext(survivedItem)[0] + ".txt" if survivedItem is not None else None,
                               os.path.relpath(os.path.join(os.path.dirname(reportPath), killedItem),
                                               os.path.dirname(reportPath)) if killedItem is not None else None,
                               killedItem, os.path.relpath(
                    os.path.join(os.path.dirname(reportPath), os.path.splitext(killedItem)[0] + ".txt"),
                    os.path.dirname(reportPath)) if killedItem is not None else None,
                               os.path.splitext(killedItem)[0] + ".txt" if killedItem is not None else None])

        fileOverallStats = "<tr><td>" + str(len(survived) + len(killed)) + " </td> <td> " + (
            "{:3.1f}%".format(float(len(killed)) / float(len(survived) + len(
                killed)) * 100)) + "  <div class=\"coverage_bar\"><div class=\"coverage_complete\" style=\"width:" + (
                                   "%d" % (float(len(killed)) / float(
                               len(survived) + len(killed)) * 100)) + "%\"></div><div class=\"coverage_legend\">" + str(
                               len(killed)) + "/" + str(len(killed) + len(survived)) + "</div></div></td></tr>"

        for item in joinedList:
            output.append(
                "<tr><td><a href=\"" + xstr(item[0]) + "\">" + xstr(item[1]) + "</a></td> <td><a href=\"" + xstr(
                    item[2]) + "\">" + xstr(item[3]) + "</a></td><td><a href=\"" + xstr(item[4]) + "\">" + xstr(
                    item[5]) + "</a></td><td><a href=\"" + xstr(item[6]) + "\">" + xstr(item[7]) + "</a></td></tr>")

        reportOutput = list()
        reportOutput.extend([reportBeginning, fileOverallStats, reportMiddle])
        reportOutput.extend(output)
        reportOutput.append(reportEnd)

        return '\n'.join(reportOutput)
