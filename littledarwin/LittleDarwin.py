from __future__ import print_function
from __future__ import division

"""
    __     _  __   __   __       ____                          _
   / /    (_)/ /_ / /_ / /___   / __ \ ____ _ _____ _      __ (_)____
  / /    / // __// __// // _ \ / / / // __ `// ___/| | /| / // // __ \
 / /___ / // /_ / /_ / //  __// /_/ // /_/ // /    | |/ |/ // // / / /
/_____//_/ \__/ \__//_/ \___//_____/ \__,_//_/     |__/|__//_//_/ /_/

Copyright (c) 2014-2020 Ali Parsai

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

Ali Parsai
www.parsai.net
ali@parsai.net

"""

# generic imports
import io
import sys
import platform
import os
from optparse import OptionParser
import shelve
import shutil
import datetime
import threading
import signal
import time
import subprocess

from builtins import str
from past.utils import old_div

### DEBUG ###


# def trace(frame, event, arg):
#     print("%s, %s:%d" % (event, frame.f_code.co_filename, frame.f_lineno))
#     return trace

# sys.settrace(trace)

#############


# LittleDarwin modules
from .JavaParse import JavaParse
from .JavaRead import JavaRead
from .JavaMutate import JavaMutate
from .ReportGenerator import ReportGenerator
from littledarwin import License


littleDarwinVersion = "0.5"


# Alternative to subprocess32

# this method uses threading backend to create a watchdog thread that kills the build system and any child processes
# after the timeout is passed.


def timeoutAlternative(commandString, workingDirectory, timeout, inputData=None):
    """

    :param commandString: command to run
    :param workingDirectory: the directory that the command is supposed to run in
    :param timeout: timeout in seconds
    :param inputData: the data that the run process may need. defaults to None.
    :return: returns kill status, process return code and the output of the system
    """

    killCheck = threading.Event()

    # this method is run in another thread when the timeout is expired to kill the process.
    def killProcess(pipe):

        assert isinstance(pipe, subprocess.Popen)

        # there is no support for os.killpg on windows, neither does it have SIGKILL.
        if platform.system() == "Windows":
            # this utility is not included in windows XP Home edition, however, there is no other alternative either.
            # therefore, don't run LittleDarwin on windows XP Home edition; he gets sad.
            subprocess.Popen("taskkill /F /T /PID %i" % pipe.pid, shell=True)
        else:
            # posix systems all support this call.
            # pipe.terminate()
            try:
                os.killpg(os.getpgid(pipe.pid), signal.SIGTERM)
            except:
                os.kill(pipe.pid, signal.SIGTERM)

        # we just killed the process. let everyone know.
        killCheck.set()

    # timeout must be int, otherwise problems arise.
    assert isinstance(timeout, int)

    # starting the process with the given parameters.
    if platform.system() != "Windows":
        process = subprocess.Popen(commandString, bufsize=1, cwd=workingDirectory, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    else:  # in Windows
        process = subprocess.Popen(commandString, bufsize=1, cwd=workingDirectory, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # passing the process and timeout references to threading's timer method, so that it kills the process
    # if timeout expires.
    timerWatchdog = threading.Timer(timeout, killProcess, args=[process])
    timerWatchdog.start()

    # do the stuff in the process.
    (stdout, stderr) = process.communicate(inputData)

    # if the process is done, no need to kill it.
    timerWatchdog.cancel()

    isKilled = killCheck.isSet()
    killCheck.clear()

    return isKilled, process.returncode, stdout


def main(argv):
    print("""
    __     _  __   __   __       ____                          _
   / /    (_)/ /_ / /_ / /___   / __ \ ____ _ _____ _      __ (_)____
  / /    / // __// __// // _ \ / / / // __ `// ___/| | /| / // // __ \\
 / /___ / // /_ / /_ / //  __// /_/ // /_/ // /    | |/ |/ // // / / /
/_____//_/ \__/ \__//_/ \___//_____/ \__,_//_/     |__/|__//_//_/ /_/

      _                     _                 ___
     /_|  /|/|  _/__/'     /_|   _ /   _ ' _ (_  _ _ _  _      _ /
    (  | /   |(//(///()/) (  |/)(/((/_) /_)  /  / (///)(-((/()/ /(
                                  /


    LittleDarwin version %s Copyright (C) 2014-2020 Ali Parsai

    LittleDarwin comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; run LittleDarwin --license for details.


    """ % littleDarwinVersion)

    # parsing input options
    optionParser = OptionParser(prog="LittleDarwin")

    optionParser.add_option("-m", "--mutate", action="store_true", dest="isMutationActive", default=False,
                            help="Activate the mutation phase.")
    optionParser.add_option("-b", "--build", action="store_true", dest="isBuildActive", default=False,
                            help="Activate the build phase.")
    optionParser.add_option("-v", "--verbose", action="store_true", dest="isVerboseActive", default=False,
                            help="Verbose output.")
    optionParser.add_option("-p", "--path", action="store", dest="sourcePath",
                            default=os.path.dirname(os.path.realpath(__file__)), help="Path to source files.")
    optionParser.add_option("-t", "--build-path", action="store", dest="buildPath",
                            default=os.path.dirname(os.path.realpath(__file__)),
                            help="Path to build system working directory.")
    optionParser.add_option("-c", "--build-command", action="store", dest="buildCommand", default="mvn,test",
                            help="Command to run the build system. If it includes more than a single argument, they should be seperated by comma. For example: mvn,install")
    optionParser.add_option("--test-path", action="store", dest="testPath",
                            default="***dummy***", help="path to test project build system working directory")
    optionParser.add_option("--test-command", action="store", dest="testCommand", default="***dummy***",
                            help="Command to run the test-suite. If it includes more than a single argument, they should be seperated by comma. For example: mvn,test")
    optionParser.add_option("--initial-build-command", action="store", dest="initialBuildCommand",
                            default="***dummy***", help="Command to run the initial build.")
    optionParser.add_option("--timeout", type="int", action="store", dest="timeout", default=60,
                            help="Timeout value for the build process.")
    optionParser.add_option("--cleanup", action="store", dest="cleanUp", default="***dummy***",
                            help="Commands to run after each build.")
    optionParser.add_option("--use-alternate-database", action="store", dest="alternateDb", default="***dummy***",
                            help="Path to alternative database.")
    optionParser.add_option("--license", action="store_true", dest="isLicenseActive", default=False,
                            help="Output the license and exit.")
    optionParser.add_option("--higher-order", type="int", action="store", dest="higherOrder", default=1,
                            help="Define order of mutation. Use -1 to dynamically adjust per class.")
    optionParser.add_option("--null-check", action="store_true", dest="isNullCheck", default=False,
                            help="Use null check mutation operators.")
    optionParser.add_option("--all", action="store_true", dest="isAll", default=False,
                            help="Use all mutation operators.")
    optionParser.add_option("--whitelist", action="store", dest="whitelist", default="***dummy***",
                            help="Analyze only included packages or files defined in this file (one package name or path to file per line).")
    optionParser.add_option("--blacklist", action="store", dest="blacklist", default="***dummy***",
                            help="Analyze everything except packages or files defined in this file (one package name or path to file per line).")

    (options, args) = optionParser.parse_args()

    if options.whitelist != "***dummy***" and options.blacklist != "***dummy***":
        print("You can either define a whitelist or a blacklist but not both.")
        sys.exit(0)

    filterList = None
    filterType = None
    if options.whitelist != "***dummy***" and os.path.isfile(options.whitelist):
        with io.open(options.whitelist, mode='r', errors='replace') as contentFile:
            filterList = contentFile.readlines()
            filterType = "whitelist"

    if options.blacklist != "***dummy***" and os.path.isfile(options.blacklist):
        with io.open(options.blacklist, mode='r', errors='replace') as contentFile:
            filterList = contentFile.readlines()
            filterType = "blacklist"

    if filterList is not None:
        filterList = [_f for _f in filterList if _f]

    if options.isLicenseActive:
        License.outputLicense()
        sys.exit(0)

    if options.higherOrder <= 1 and options.higherOrder != -1:
        higherOrder = 1
    else:
        higherOrder = options.higherOrder

    # there is an upside in not running two phases together. we may include the ability to edit some mutants later.
    if options.isBuildActive and options.isMutationActive:
        print("it is strongly recommended to do the analysis in two different phases.\n\n")

    # *****************************************************************************************************************
    # ---------------------------------------- mutant generation phase ------------------------------------------------
    # *****************************************************************************************************************

    if options.isMutationActive:
        assert options.isVerboseActive is not None
        # creating our module objects.
        javaRead = JavaRead(options.isVerboseActive)
        javaParse = JavaParse(options.isVerboseActive)
        javaMutate = JavaMutate(javaParse, options.isVerboseActive)

        totalMutantCount = 0

        try:
            assert os.path.isdir(options.sourcePath)
        except AssertionError as exception:
            print("source path must be a directory.")
            sys.exit(1)

        # getting the list of files.
        javaRead.listFiles(targetPath=os.path.abspath(options.sourcePath), buildPath=os.path.abspath(options.buildPath),
                           filterType=filterType, filterList=filterList)
        fileCounter = 0
        fileCount = len(javaRead.fileList)

        # creating a database for generated mutants. the format of this database is different on different platforms,
        # so it cannot be simply copied from a platform to another.
        databasePath = os.path.join(javaRead.targetDirectory, "mutationdatabase")

        print("source dir: ", javaRead.sourceDirectory)
        print("target dir: ", javaRead.targetDirectory)
        print("creating mutation database: ", databasePath)

        mutationDatabase = shelve.open(databasePath, "c")
        mutantTypeDatabase = dict()

        # go through each file, parse it, calculate all mutations, and generate files accordingly.
        for srcFile in javaRead.fileList:
            print("(" + str(fileCounter + 1) + "/" + str(fileCount) + ") source file: ", srcFile)
            targetList = list()

            try:
                # parsing the source file into a tree.
                tree = javaParse.parse(javaRead.getFileContent(srcFile))

                # assigning a number to each node to be able to identify it uniquely.
                javaParse.numerify(tree)
                # javaParse.tree2DOT(tree)

            except Exception as e:
                # Java 8 problem
                print("Error in parsing, skipping the file.")
                sys.stderr.write(e.message)
                continue

            fileCounter += 1

            if options.isAll:
                enabledMutators = "all"
            elif options.isNullCheck:
                enabledMutators = "null-check"
            else:
                enabledMutators = "classical"

            # apply mutations on the tree and receive the resulting mutants as a list of strings, and a detailed
            # list of which operators created how many mutants.
            javaMutate.mutantsPerLine = dict()
            mutated, mutantTypes = javaMutate.applyMutators(tree, higherOrder, enabledMutators)

            print("--> mutations found: ", len(mutated))

            # go through all mutant types, and add them in total. also output the info to the user.
            for mutantType in list(mutantTypes.keys()):
                if mutantTypes[mutantType] > 0:
                    print("---->", mutantType, ":", mutantTypes[mutantType])
                mutantTypeDatabase[mutantType] = mutantTypes[mutantType] + mutantTypeDatabase.get(mutantType, 0)
            totalMutantCount += len(mutated)

            # for each mutant, generate the file, and add it to the list.
            for mutatedFile in mutated:
                targetList.append(javaRead.generateNewFile(srcFile, mutatedFile, javaMutate.mutantsPerLine))

            # if the list is not empty (some mutants were found), put the data in the database.
            if len(targetList) != 0:
                mutationDatabase[os.path.relpath(srcFile, javaRead.sourceDirectory)] = targetList

        mutationDatabase.close()

        print("total mutations found: ", totalMutantCount)
        for mutantType in list(mutantTypeDatabase.keys()):
            if mutantTypeDatabase[mutantType] > 0:
                print("-->", mutantType, ":", mutantTypeDatabase[mutantType])

    # *****************************************************************************************************************
    # ---------------------------------------- test suite running phase -----------------------------------------------
    # *****************************************************************************************************************

    if options.isBuildActive:

        # let's tell the user upfront that this may corrupt the source code.
        print("\n\n!!! CAUTION !!!")
        print("code can be changed accidentally. use a backup version.\n")

        reportGenerator = ReportGenerator(littleDarwinVersion)

        if options.alternateDb == "***dummy***":
            databasePath = os.path.abspath(os.path.join(options.buildPath, "LittleDarwinResults", "mutationdatabase"))
        else:
            databasePath = options.alternateDb

        mutantsPath = os.path.dirname(databasePath)
        assert os.path.isdir(mutantsPath)

        resultsDatabasePath = databasePath + "-results"
        reportGenerator.initiateDatabase(resultsDatabasePath)

        try:
            if os.path.basename(options.buildPath) == "pom.xml":
                assert os.path.isfile(options.buildPath)
                buildDir = os.path.abspath(os.path.dirname(options.buildPath))
            else:
                assert os.path.isdir(options.buildPath)
                buildDir = os.path.abspath(options.buildPath)

        except AssertionError as exception:
            print("build system working directory should be a directory.")

        # check if we have separate test-suite
        if options.testCommand != "***dummy***":
            separateTestSuite = True
            if options.testPath == "***dummy***":
                testDir = buildDir
            else:
                try:
                    if os.path.basename(options.buildPath) == "pom.xml":
                        assert os.path.isfile(options.buildPath)
                        testDir = os.path.abspath(os.path.dirname(options.testPath))
                    else:
                        assert os.path.isdir(options.buildPath)
                        testDir = os.path.abspath(options.testPath)

                except AssertionError as exception:
                    print("test project build system working directory should be a directory.")

        else:
            separateTestSuite = False

        # try to open the database. if it can't be opened, it means that it does not exist or it is corrupt.
        try:
            mutationDatabase = shelve.open(databasePath, "r")
        except:
            print("cannot open mutation database. it may be corrupted or unavailable. delete all generated files and run the mutant generation phase again.")
            sys.exit(1)

        databaseKeys = list(mutationDatabase.keys())
        assert isinstance(databaseKeys, list)

        # let's sort the mutants by name to create the possibility of following the flow of the process by user.
        databaseKeys.sort()

        # only here for debugging purposes
        # for desired in databaseKeys:
        #     if "PluginMap.java" in desired:
        #         desiredIndex = databaseKeys.index(desired)
        #         break
        #
        # databaseKeys.insert(0, databaseKeys.pop(desiredIndex))
        #

        mutationDatabaseLength = len(databaseKeys)
        textReportData = list()
        htmlReportData = list()
        fileCounter = 0

        # initial build check to avoid false results. the system must be able to build cleanly without errors.

        # use build command for the initial build unless it is explicitly provided.
        if options.initialBuildCommand == "***dummy***":
            commandString = options.buildCommand.split(',')
        else:
            commandString = options.initialBuildCommand.split(',')

        print("Initial build... ",)

        try:
            processKilled, processExitCode, initialOutput = timeoutAlternative(commandString,
                                                                               workingDirectory=buildDir,
                                                                               timeout=int(options.timeout))

            # initialOutput = subprocess.check_output(commandString, stderr=subprocess.STDOUT, cwd=buildDir)
            # workaround for older python versions
            if processKilled or processExitCode:
                raise subprocess.CalledProcessError(1 if processKilled else processExitCode, commandString,
                                                    initialOutput)

            with open(os.path.abspath(os.path.join(mutantsPath, "initialbuild.txt")), 'w') as contentFile:
                contentFile.write(str(initialOutput))
            print("done.\n\n")

        except subprocess.CalledProcessError as exception:
            initialOutput = exception.output
            with open(os.path.abspath(os.path.join(mutantsPath, "initialbuild.txt")), 'w') as contentFile:
                contentFile.write(str(initialOutput))

            print("failed.\n")
            print("Initial build failed. Try building the system manually first to make sure it can be built. Take a look at " + os.path.abspath(
                os.path.join(mutantsPath, "initialbuild.txt")) + " to find out why this happened.")
            sys.exit(1)

        totalMutantCount = 0
        totalMutantCounter = 0

        for key in databaseKeys:
            totalMutantCount += len(mutationDatabase[key])

        startTime = time.time()

        # running the build system for each mutant.
        for key in databaseKeys:

            fileCounter += 1

            print("(" + str(fileCounter) + "/" + str(mutationDatabaseLength) + ") collecting results for ", key)

            mutantCount = len(mutationDatabase[key])
            mutantCounter = 0

            successList = list()
            failureList = list()

            # for each mutant, replace the original file, run the build, store the results
            for replacementFileRel in mutationDatabase[key]:
                replacementFile = os.path.abspath(os.path.join(mutantsPath, replacementFileRel))
                mutantCounter += 1
                totalMutantCounter += 1

                # let's make sure that runOutput is empty, and not None to begin with.
                runOutput = bytes()
                runOutputTest = bytes()

                # replace the original file with the mutant
                shutil.copyfile(replacementFile, os.path.join(options.sourcePath, key))

                commandString = options.buildCommand.split(',')
                if separateTestSuite:
                    testCommandString = options.testCommand.split(',')

                try:
                    # if we have timeout support, simply run the command with timeout support from subprocess32
                    # if timeoutSupport:
                    #     runOutput = subprocess.check_output(commandString, stderr=subprocess.STDOUT, cwd=buildDir,
                    #                                         timeout=int(options.timeout))
                    #     if separateTestSuite:
                    #         runOutput += subprocess.check_output(testCommandString, stderr=subprocess.STDOUT, cwd=testDir,
                    #                                         timeout=int(options.timeout))

                    # else, run our alternative method
                    # else:
                    processKilled, processExitCode, runOutput = timeoutAlternative(commandString,
                                                                                   workingDirectory=buildDir,
                                                                                   timeout=int(options.timeout))

                    # raise the same exception as the original check_output.
                    if processKilled or processExitCode:
                        raise subprocess.CalledProcessError(1 if processKilled else processExitCode, commandString,
                                                            runOutput)

                    if separateTestSuite:
                        processKilled, processExitCode, runOutputTest = timeoutAlternative(testCommandString,
                                                                                           workingDirectory=testDir,
                                                                                           timeout=int(options.timeout))

                        # raise the same exception as the original check_output.
                        if processKilled or processExitCode:
                            raise subprocess.CalledProcessError(1 if processKilled else processExitCode,
                                                                commandString, "\n".join([runOutput, runOutputTest]))

                    # if we are here, it means no exceptions happened, so lets add this to our success list.
                    runOutput = runOutput.decode("utf-8") + '\n' + runOutputTest.decode("utf-8")
                    successList.append(os.path.basename(replacementFile))

                # putting two exceptions in one except clause, specially when one of them is not defined on some
                # platforms does not look like a good idea; even though both of them do exactly the same thing.
                except subprocess.CalledProcessError as exception:
                    runOutput = exception.output.decode("utf-8")
                    # oops, error. let's add this to failure list.
                    failureList.append(os.path.basename(replacementFile))

                # except subprocess.TimeoutExpired as exception:
                #     runOutput = exception.output
                #     failureList.append(os.path.basename(replacementFile))

                targetTextOutputFile = os.path.splitext(replacementFile)[0] + ".txt"

                # we can't use print, since we like to write on the same line again.
                sys.stdout.write(
                    "elapsed: " + str(datetime.timedelta(seconds=int(time.time() - startTime))) + " remaining: " + str(
                        datetime.timedelta(seconds=int((old_div(float(time.time() - startTime), totalMutantCounter)) * float(
                            totalMutantCount - totalMutantCounter)))) + " total: " + str(
                        totalMutantCounter) + "/" + str(totalMutantCount) + " current: " + str(
                        mutantCounter) + "/" + str(mutantCount) + " *** survived: " + str(
                        len(successList)) + " - killed: " + str(len(failureList)) + "         \r")
                sys.stdout.flush()

                # writing the build output to disk.
                with open(targetTextOutputFile, 'w') as contentFile:
                    contentFile.write(str(runOutput))

                # if there's a cleanup option, execute it. the results will be ignored because we don't want our process
                #  to be interrupted if there's nothing to clean up.
                if options.cleanUp != "***dummy***":
                    subprocess.call(options.cleanUp.split(","), cwd=buildDir)
                    if separateTestSuite:
                        subprocess.call(options.cleanUp.split(","), cwd=testDir)

                # workaround:
                # shutil.rmtree(os.path.join(testDir,"VolumetryLoggerTest"),ignore_errors=True)

            # all mutants must be checked by now, so we should have a complete divide between success and failure.
            assert len(successList) + len(failureList) == mutantCount

            # append the information for this file to the reports.
            textReportData.append(key + ": survived (" + str(len(successList)) + "/" + str(mutantCount) + ") -> " + str(
                successList) + " - killed (" + str(len(failureList)) + "/" + str(mutantCount) + ") -> " + str(
                failureList) + "\r\n")
            htmlReportData.append([key, len(successList), mutantCount])

            # we are done with the file. let's return it to the original state.
            shutil.copyfile(os.path.join(os.path.dirname(replacementFile), "original.java"),
                            os.path.join(options.sourcePath, key))

            # generate an HTML report for the file.

            targetHTMLOutputFile = os.path.join(os.path.dirname(replacementFile), "results.html")
            with open(targetHTMLOutputFile, 'w') as contentFile:
                contentFile.write(
                    reportGenerator.generateHTMLReportPerFile(key, targetHTMLOutputFile, successList, failureList))

            print("\n\n")

        # write final text report.
        with open(os.path.abspath(os.path.join(mutantsPath, "report.txt")),
                  'w') as textReportFile:
            textReportFile.writelines(textReportData)

        # write final HTML report.
        targetHTMLReportFile = os.path.abspath(
            os.path.join(mutantsPath, "report.html"))
        with open(targetHTMLReportFile, 'w') as htmlReportFile:
            htmlReportFile.writelines(reportGenerator.generateHTMLFinalReport(htmlReportData, targetHTMLReportFile))

    # if neither build nor mutation phase is active, let's help the user.
    if not (options.isBuildActive or options.isMutationActive):
        optionParser.print_help()
        print("\nExample:\n  LittleDarwin -m -b -t ./ -p ./src/main -c mvn,clean,test --timeout=120\n\n")


