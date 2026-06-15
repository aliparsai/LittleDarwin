import sys
import io
from typing import Any
import networkx as nx
import dill
import time
import datetime
import re
import itertools
import os
from mediumdarwin.JavaMutate import Mutation
from unicurses import *
from pathlib import Path
import importlib_resources as resources
from joblib import Parallel, delayed
from optparse import OptionParser
from antlr4.tree.Tree import TerminalNodeImpl
from colorama import Fore, Style
from antlr4 import Token
from mediumdarwin.LineCoverage import LineCoverage
from mediumdarwin import License
from mediumdarwin.JavaIO import JavaIO
from mediumdarwin.JavaParse import JavaParse
from mediumdarwin.JavaMutate import JavaMutate, LogicalOperatorReplacement, ConditionalOperatorReplacement, HOM
from mediumdarwin.Database import Database
from mediumdarwin.JavaParser import JavaParser
from mediumdarwin.SharedFunctions import *
from mediumdarwin.JavaMutate import (
    recursiveCloneANTLRNodeAndItsChildren,
    replaceNodes,
    findNodesWithMutationID
)
import subprocess


def parseCmdArgs(optionParser: OptionParser, mockArgs: list = None) -> object:
    """

    :param mockArgs:
    :type mockArgs:
    :param optionParser:
    :type optionParser:
    :return:
    :rtype:
    """

    # mutation list option
    optionParser.add_option(
        "--mutation-ids",
        action="store",
        dest="mutationIds",
        default="***dummy***",
        help="Comma-separated list of mutation IDs to generate a single mutant with (e.g., '4, 5, 6').",
    )

    optionParser.add_option(
        "--reset",
        action="store_true",
        dest="reset",
        default=False,
        help="Reset the project by returning to the initial state.",
    )
    # parsing input options
    optionParser.add_option(
        "-m",
        "--mutate",
        action="store_true",
        dest="isMutationActive",
        default=False,
        help="Activate the mutation phase.",
    )

    optionParser.add_option(
        "--fail_string",
        action="store",
        dest="fail_string",
        default=None,
        help="The string to search in the stdout of the build system to determine if the build has failed.",
    )

    optionParser.add_option(
        "-b",
        "--build",
        action="store_true",
        dest="isBuildActive",
        default=False,
        help="Activate the build phase.",
    )

    optionParser.add_option(
        "-q",
        "--code_coverage",
        action="store_true",
        dest="isCoverageActive",
        default=False,
        help="Run code coverage analysis and exclude tests from mutation.",
    )

    optionParser.add_option(
        "--run_all_tests",
        action="store_true",
        dest="runAllTests",
        default=False,
        help="Should the tool stop after the first failing test?",
    )

    optionParser.add_option(
        "--test_target_name",
        action="store",
        dest="testTargetName",
        default="test",
        help="Set the test target name for ant.",
    )

    optionParser.add_option(
        "--junit_target_name",
        action="store",
        dest="junitTargetName",
        default="internal-test",
        help="Set the junit target name for ant.",
    )

    optionParser.add_option(
        "-v",
        "--verbose",
        action="store_true",
        dest="isVerboseActive",
        default=False,
        help="Verbose output.",
    )
    optionParser.add_option(
        "--cleanup",
        action="store",
        dest="cleanUp",
        default="***dummy***",
        help="Commands to run after each build.",
    )

    optionParser.add_option(
        "-p",
        "--path",
        action="store",
        dest="sourcePath",
        default=os.path.dirname(os.path.realpath(__file__)),
        help="Path to source files.",
    )

    optionParser.add_option(
        "-t",
        "--build-path",
        action="store",
        dest="buildPath",
        default=os.path.dirname(os.path.realpath(__file__)),
        help="Path to build system working directory.",
    )

    optionParser.add_option(
        "-c",
        "--build-command",
        action="store",
        dest="buildCommand",
        default="mvn,test",
        help="Command to run the build system. If it includes more than a single argument, they should be seperated by comma. For example: mvn,install",
    )

    optionParser.add_option(
        "--test-path",
        action="store",
        dest="testPath",
        default="***dummy***",
        help="path to test project build system working directory",
    )
    optionParser.add_option(
        "--test-command",
        action="store",
        dest="testCommand",
        default="***dummy***",
        help="Command to run the test-suite. If it includes more than a single argument, they should be seperated by comma. For example: mvn,test",
    )

    optionParser.add_option(
        "--initial-build-command",
        action="store",
        dest="initialBuildCommand",
        default="***dummy***",
        help="Command to run the initial build.",
    )
    optionParser.add_option(
        "--timeout",
        type="int",
        action="store",
        dest="timeout",
        default=60,
        help="Timeout value for the mutants.",
    )

    optionParser.add_option(
        "--initial-timeout",
        type="int",
        action="store",
        dest="initial_timeout",
        help="Timeout value for the initial test/build process (default is double the mutation timeout).",
    )

    optionParser.add_option(
        "--use-alternate-database",
        action="store",
        dest="alternateDb",
        default="***dummy***",
        help="Path to alternative database.",
    )
    optionParser.add_option(
        "--license",
        action="store_true",
        dest="isLicenseActive",
        default=False,
        help="Output the license and exit.",
    )
    optionParser.add_option(
        "--higher-order",
        type="int",
        action="store",
        dest="higherOrder",
        default=1,
        help="Define order of mutation. Use -1 to dynamically adjust per class.",
    )
    optionParser.add_option(
        "--jobs-no",
        type="int",
        action="store",
        dest="numberOfJobs",
        default=1,
        help="Choose the number of jobs that you want to have for the purpose of parallelization.",
    )
    optionParser.add_option(
        "--null-check",
        action="store_true",
        dest="isNullCheck",
        default=False,
        help="Use null check mutation operators.",
    )
    optionParser.add_option(
        "--method-level",
        action="store_true",
        dest="isMethodLevel",
        default=False,
        help="Use method level mutation operators.",
    )
    optionParser.add_option(
        "--all",
        action="store_true",
        dest="isAll",
        default=False,
        help="Use all mutation operators.",
    )
    optionParser.add_option(
        "--whitelist",
        action="store",
        dest="whitelist",
        default="***dummy***",
        help="Analyze only included packages or files defined in this file (one package name or path to file per line).",
    )
    optionParser.add_option(
        "--blacklist",
        action="store",
        dest="blacklist",
        default="***dummy***",
        help="Analyze everything except packages or files defined in this file (one package name or path to file per line).",
    )

    optionParser.add_option(
        "-s",
        "--subsumption",
        action="store_true",
        dest="isSubsumptionActive",
        default=False,
        help="Subsumption analysis output.",
    )

    optionParser.add_option(
        "-e",
        "--schemata",
        action="store_true",
        dest="isSchemataActive",
        default=False,
        help="Mutant Schemata.",
    )

    optionParser.add_option(
        "--compile_failure_regex",
        action="store",
        dest="compile_failure_regex",
        default=r"^(.+\.java):(\d+):\s*error:.*",
        help=("Regex to detect compile failures in schemata generation. "
              "It should match compile errors and contain either: "
              "(a) two groups: 1) the path to the java file with the error, 2) the line number "
              "(column will be derived from the caret '^' line), or "
              "(b) three groups: 1) file path, 2) line number, 3) column number.")
    )
    optionParser.add_option(
        "-H",
        "--help-me",
        action="store_true",
        dest="help_me",
        default=False,
        help="print help.",
    )
    optionParser.add_option(
        "--mutation-ids-file",
        action="store",
        dest="mutationIdsFile",
        default="***dummy***",
        help="Path to a file containing multiple HOM definitions, one per line. Each line should contain comma-separated mutation IDs (e.g., '1, 2, 3, 4' on first line, '5, 6, 7' on second line).",
    )
    if mockArgs is None:
        (options, args) = optionParser.parse_args()
    else:
        (options, args) = optionParser.parse_args(args=mockArgs)

    if options.help_me:
        print(r"""
              Usage: script.py [options]

              Options:
                --reset                    Reset the project to the initial state.
                -m, --mutate              Activate the mutation phase.
                --fail_string STR         String to detect build failure from stdout.
                -b, --build               Activate the build phase.
                -q, --code_coverage       Run code coverage analysis.
                --run_all_tests           Run all tests instead of stopping after the first failure.
                --test_target_name NAME   Ant target name for running tests (default: test).
                --junit_target_name NAME  Ant target name for JUnit (default: internal-test).
                -v, --verbose             Enable verbose output.
                --cleanup CMD             Commands to run after each build.
                -p, --path PATH           Path to source files.
                -t, --build-path PATH     Path to build system working directory.
                -c, --build-command CMD   Build command (comma-separated if multiple).
                --test-path PATH          Path to test project build system directory.
                --test-command CMD        Test command (comma-separated if multiple).
                --initial-build-command CMD  Command for initial build.
                --timeout SEC             Timeout for mutant execution (default: 60).
                --initial-timeout SEC     Timeout for initial build/test phase (default: 2x mutation timeout).
                --use-alternate-database PATH  Path to alternate database.
                --license                 Display license and exit.
                --higher-order INT        Mutation order (default: 1; use -1 for dynamic).
                --jobs-no INT             Number of parallel jobs (default: 1).
                --null-check              Use null check mutation operators.
                --method-level            Use method-level mutation operators.
                --all                     Use all mutation operators.
                --whitelist FILE          Whitelisted packages/files (one per line).
                --blacklist FILE          Blacklisted packages/files (one per line).
                -s, --subsumption         Enable subsumption analysis output.
                -e, --schemata            Enable mutant schemata generation.
                --compile_failure_regex REGEX  Regex to detect compile failures in schemata generation. It should match compile errors and contain three groups: 1) the path to the java file with the error, 2) the line number, and 3) the column number.
                --mutation-ids IDS        Comma-separated list of mutation IDs to generate a single mutant with (e.g., '4, 5, 6').
                --mutation-ids-file FILE Path to a file containing multiple HOM definitions, one per line. Each line should contain comma-separated mutation IDs (e.g., '1, 2, 3, 4' on first line, '5, 6, 7' on second line).


              Note:
              - You can specify either a whitelist or a blacklist, not both.
              - If both --build and --mutate are active, it's recommended to run them in separate phases.

              Example:
                MediumDarwin.py -m -b --build-command "mvn,install" --timeout 90
              """)
        sys.exit(0)

    if options.initial_timeout is None:
        options.initial_timeout = int(options.timeout) * 2
    if options.whitelist != "***dummy***" and options.blacklist != "***dummy***":
        print("You can either define a whitelist or a blacklist but not both.")
        sys.exit(4)
    filterList = None
    filterType = None
    if options.whitelist != "***dummy***" and os.path.isfile(options.whitelist):
        with io.open(options.whitelist, mode="r", errors="replace") as contentFile:
            filterList = [l.strip() for l in contentFile.readlines()]
            filterType = "whitelist"
    if options.blacklist != "***dummy***" and os.path.isfile(options.blacklist):
        with io.open(options.blacklist, mode="r", errors="replace") as contentFile:
            filterList = [l.strip() for l in contentFile.readlines()]
            filterType = "blacklist"
    if filterList is not None:
        filterList = [_f for _f in filterList if _f]
    if options.isLicenseActive:
        License.outputLicense()
        sys.exit(0)
    if options.higherOrder < 1:  # and options.higherOrder != -1:
        print("Order cannot be smaller than 1.")
        sys.exit(4)
    else:
        higherOrder = options.higherOrder
    # there is an upside in not running two phases together. we may include the ability to edit some mutants later.
    if options.isBuildActive and options.isMutationActive:
        print(
            "it is strongly recommended to do mutant generation, mutant execution, and subsumption analysis in different phases.\n\n"
        )
    return options, filterType, filterList, higherOrder


class Schemata:
    littleDarwinVersion = "0.10.7"
    clean_time = 0
    compile_time = 0
    test_time = 0
    _GOOGLE_JAVA_FORMAT_JAR = "google-java-format-1.7-all-deps.jar"

    def _emit_formatter_warning(self, message: str) -> None:
        if getattr(self, "_formatter_warning_emitted", False):
            return
        print(f"[WARN] {message}")
        self._formatter_warning_emitted = True

    def _format_java_file(self, java_file_path: str) -> None:
        if not java_file_path or not os.path.isfile(java_file_path):
            return
        try:
            formatter_resource = (
                resources.files("mediumdarwin")
                .joinpath("jar")
                .joinpath(self._GOOGLE_JAVA_FORMAT_JAR)
            )
            with resources.as_file(formatter_resource) as jar_path:
                completed = subprocess.run(
                    ["java", "-jar", str(jar_path), "-i", java_file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            if completed.returncode != 0:
                stderr = completed.stderr.strip() if completed.stderr else ""
                self._emit_formatter_warning(
                    f"google-java-format exited with code {completed.returncode} for {java_file_path}. {stderr}"
                )
        except FileNotFoundError as exc:
            self._emit_formatter_warning(
                f"Unable to run google-java-format for {java_file_path}: {exc}"
            )
        except Exception as exc:
            self._emit_formatter_warning(
                f"google-java-format failed for {java_file_path}: {exc}"
            )

    def subsumptionAnalysisPhase(self, options: object) -> None:
        mutationDatabase = Database(self.sqlDBPath)
        mutationDatabase.delete_data("mutant_test", "result!="+str(Database.RES_ID_BUILD_FAILURE) +
                                     " AND result!="+str(Database.RES_ID_NON_COVERED) +
                                     " AND result!="+str(Database.RES_ID_TIMEOUT))

        self.updateMutationTestTable(options, mutationDatabase)
        self.createMutantTestMatrix(options, mutationDatabase)

    def updateMutationTestTable(self, options: object, mutationDatabase, file_name=None, mutant_id=None) -> None:
        if file_name == None and mutant_id == None:
            file_muants = mutationDatabase.fetch_mutants(options=options)
        else:
            file_muants = mutationDatabase.fetch_file_mutant_with_id(
                file_name=file_name, mutant_id=mutant_id, options=options)
        tests = mutationDatabase.fetch_data("test")
        test_dict = {}
        for test in tests:
            # At this stage we do not need to have test case method or class separated
            test = list(test)
            test[1] = test[1].replace("$", ".")
            test[1] = test[1].replace("#", ".")
            test_dict[test[1]] = test[0]

        def return_values(file, debug=False):
            '''
            return values to be inserted to the db later.
            '''
            nonlocal test_dict

            if debug:
                print_str = "extracting test data from: " + file
                print("".join(["-"] * len(print_str)))
                print(print_str)
            xml_files.append(file)
            results = parse_junit_xml(file)

            values = []
            for result in results:
                test_res = Database.RES_ID_SURVIVED_MUTANT
                error_msg = ""
                if result[2] != "":
                    error_msg = result[2]
                    test_res = Database.RES_ID_KILLED_BY_FAILURE_MUTANT
                elif result[3] != "":
                    error_msg = result[3]
                    test_res = Database.RES_ID_KILLED_BY_ERROR_MUTANT

                if result[0] in test_dict:
                    values.append((file_mutant[1],
                                   test_dict[result[0]],
                                   test_res,
                                   result[1],
                                   error_msg))
                else:
                    values.append((file_mutant[1],
                                   str(Database.NO_TEST),
                                   test_res,
                                   result[1],
                                   error_msg))
            return values

        for file_mutant in file_muants:
            fileRelativePath = os.path.join(
                self.LittleDarwinResultsPath,
                os.path.relpath(file_mutant[0], options.sourcePath),
            )
            directory = str(
                os.path.join(
                    fileRelativePath,
                    str(file_mutant[1]) + "-test_reports",
                )
            )
            xml_files = []
            if os.path.exists(directory):
                values = []
                for xml_file in glob(str(os.path.join(directory, "**", "*.xml")), recursive=True):
                    values_ = return_values(xml_file)
                    values.extend(values_)
                mutationDatabase.insert_many(
                    "mutant_test", "mutant_id, test_id, result, time, message", values)
            else:
                mutationDatabase.insert_data(
                    "mutant_test",
                    "mutant_id, test_id, result, time, message",
                    [
                        file_mutant[1],
                        Database.NO_INFO,
                        Database.RES_ID_BUILD_FAILURE,
                        "0",
                        "no results found. Most probably compilation error.",
                    ],
                )
        # use this sql query to get the records of the mutants that have caused compilation errors:
        # SELECT * FROM mutant_test join mutant on mutant.id=mutant_test.mutant_id join mutation on mutation.id=mutant.mutation_id join mutation_operator on mutation_operator.id=mutation.mutation_operator_id WHERE result=-1;

    def createMutantTestMatrix(self, options: object, mutationDatabase) -> None:
        mutant_tests = mutationDatabase.fetch_data(
            "mutant_test", "*", "result!=" +
            str(Database.RES_ID_SURVIVED_MUTANT) +
            " AND result!="+str(Database.RES_ID_BUILD_FAILURE) +
            " AND result!="+str(Database.RES_ID_NON_COVERED) +
            " AND result!="+str(Database.RES_ID_TIMEOUT)
        )  # exclude surviving and build failure and non-covered ones
        mutant_test_dict = {}
        test_mutant_dict = {}
        for mutant_test in mutant_tests:
            if mutant_test[0] not in mutant_test_dict:
                mutant_test_dict[mutant_test[0]] = set()
            mutant_test_dict[mutant_test[0]].add(mutant_test[1])
            if mutant_test[1] not in test_mutant_dict:
                test_mutant_dict[mutant_test[1]] = set()
            test_mutant_dict[mutant_test[1]].add(mutant_test[0])
        G = nx.DiGraph()
        for mutant in mutant_test_dict.keys():
            for mutant2 in mutant_test_dict.keys():
                if G.has_node(str(mutant)) == False:
                    G.add_node(str(mutant))
                    G.nodes[str(mutant)]["label"] = str(mutant)

                if G.has_node(str(mutant2)) == False:
                    G.add_node(str(mutant2))
                    G.nodes[str(mutant2)]["label"] = str(mutant2)

                if mutant_test_dict[mutant].issubset(mutant_test_dict[mutant2]):
                    if (
                        str(mutant) != str(mutant2)
                        and G.has_edge(str(mutant), str(mutant2)) == False
                    ):
                        if (
                            mutant_test_dict[mutant] == mutant_test_dict[mutant2]
                        ):  # equal test sets
                            G.add_edge(str(mutant), str(mutant2), color="red")
                            print(
                                Fore.RED + str(mutant) +
                                " ---> " + str(mutant2),
                            )
                            print(
                                str(mutant_test_dict[mutant])
                                + " ---> "
                                + str(mutant_test_dict[mutant2])
                            )
                            print(Style.RESET_ALL)
                        else:  # subset test sets
                            G.add_edge(str(mutant), str(mutant2), color="blue")
                            print(
                                Fore.BLUE + str(mutant) +
                                " ---> " + str(mutant2),
                            )
                            print(
                                str(mutant_test_dict[mutant])
                                + " ---> "
                                + str(mutant_test_dict[mutant2])
                            )
                            print(Style.RESET_ALL)
                        print("-----------------------------------")

        # Contracting nodes mutates the graph (removes/merges nodes + edges).
        # Iterating NetworkX views while mutating can yield stale (u, v) pairs,
        # which then triggers KeyError when indexing G.edges[u, v].
        #
        # Instead: repeatedly take a snapshot of current "red" edges and contract them.
        changed = True
        while changed:
            changed = False
            red_edges = [(u, v) for (u, v, d) in G.edges(
                data=True) if d.get("color") == "red"]
            if not red_edges:
                break
            for u, v in red_edges:
                if u not in G or v not in G or not G.has_edge(u, v):
                    continue
                # Merge labels before contracting away v into u
                G.nodes[u]["label"] = f"{G.nodes[u].get('label', str(u))}, {G.nodes[v].get('label', str(v))}"
                G = nx.contracted_nodes(G, u, v, self_loops=False)
                changed = True

        TR = nx.transitive_reduction(G)

        mapping = {}
        for node in TR.nodes:
            if TR.in_degree(node) == 0:
                TR.nodes[node]["color"] = "green"
                print(Fore.GREEN + " d(" + str(node) + ") =" +
                      str(G.out_degree(node)))
            mapping[node] = G.nodes[node]["label"]

        print(Style.RESET_ALL)
        TR = nx.relabel_nodes(TR, mapping)
        dot_string_alt = nx.nx_pydot.to_pydot(TR).to_string()

        nx.write_gml(
            TR,
            os.path.join(self.LittleDarwinResultsPath,
                         "subsumption_graph.gml"),
            stringizer=str,
        )
        nx.write_pajek(
            TR,
            os.path.join(self.LittleDarwinResultsPath,
                         "subsumption_graph.gml"),
        )
        # Also persist the labeled graph in modern formats (optional for downstream tools)
        try:
            nx.write_gpickle(
                TR,
                os.path.join(self.LittleDarwinResultsPath,
                             "dmsg_labeled.gpickle"),
            )
        except Exception:
            pass
        try:
            nx.write_graphml(
                TR,
                os.path.join(self.LittleDarwinResultsPath,
                             "dmsg_labeled.graphml"),
            )
        except Exception:
            pass
        try:
            nx.write_gexf(
                TR,
                os.path.join(self.LittleDarwinResultsPath,
                             "dmsg_labeled.gexf"),
            )
        except Exception:
            pass
        with open(os.path.join(self.LittleDarwinResultsPath, "subsumption_graph.dot"), "w") as file:
            file.write(dot_string_alt)

    def run_test(
        self,
        mutant_id: int,
        mutation: list,
        test_command: list,
        source_directory: str,
        targetTextOutputFile: str = "",
        coverage: bool = False,
        file: str = "",
        timeout=120,
        fail_message="FAILED",
        debug=False,
    ):
        """
        A wrapper function to run the test command in parallel

        mutation: the list of the mutations to be activated;
        test_command: the test command to be executed;
        source_directory: the project's directory
        """
        (
            process_test_killed,
            process_test_exit_code,
            run_output_test,
            time_delta
        ) = timeoutAlternative(
            commandString=test_command.copy(),
            workingDirectory=source_directory,
            timeout=timeout,
            failMessage=fail_message,
            activeMutants=mutation,
        )
        file_name = return_build_file(" ".join(test_command))
        backupFile = None
        buildType = ""
        root_, file_ = os.path.split(targetTextOutputFile)
        path = Path(root_)
        buildType = detect_build_tool(test_command[0])
        # Gradle build scripts are not rewritten per mutant. Backing them up per mutant is noisy and
        # not parallel-friendly, so we skip build-file backups entirely for Gradle.
        if buildType == "gradle":
            file_name = None
            backupFile = None
        if file_name == None:
            if buildType == "ant":
                file_name = os.path.join(source_directory, "build.xml")
                backupFile = os.path.join(
                    path.absolute(),
                    str(mutant_id) + ".build.xml",
                )
            elif buildType == "mvn":
                file_name = os.path.join(source_directory, "pom.xml")
                backupFile = os.path.join(
                    path.absolute(),
                    str(mutant_id) + ".pom.xml",
                )
            elif buildType == "gradle":
                groovy = os.path.join(source_directory, "build.gradle")
                kotlin = os.path.join(source_directory, "build.gradle.kts")
                if os.path.isfile(groovy):
                    file_name = groovy
                    backupFile = os.path.join(
                        path.absolute(),
                        str(mutant_id) + ".build.gradle",
                    )
                elif os.path.isfile(kotlin):
                    file_name = kotlin
                    backupFile = os.path.join(
                        path.absolute(),
                        str(mutant_id) + ".build.gradle.kts",
                    )
                else:
                    file_name = None
                    backupFile = None
        else:
            if buildType == "ant":
                backupFile = os.path.join(
                    path.absolute(),
                    str(mutant_id) + ".build.xml",
                )
            elif buildType == "mvn":
                backupFile = os.path.join(
                    path.absolute(),
                    str(mutant_id) + ".pom.xml",
                )
            elif buildType == "gradle":
                backupFile = os.path.join(
                    path.absolute(),
                    str(mutant_id) + ".build.gradle",
                )
        if debug:
            print("mutation: " + repr(mutation))
            print("test command: " + " ".join(test_command))
        if file_name is None or backupFile is None or (not os.path.isfile(file_name)):
            if buildType != "gradle":
                print("build file not found no backup is taken")
        else:
            # Ensure destination folder exists. IMPORTANT: this function can run in parallel.
            # Never move shared build files (e.g., build.gradle/pom.xml/build.xml) because it
            # makes concurrent workers fail with "build file not found". Always copy instead.
            os.makedirs(path.absolute(), exist_ok=True)
            if debug:
                print("copying: " + file_name + " -> " + backupFile)
            shutil.copy2(file_name, backupFile)
        with open(targetTextOutputFile, "w") as contentFile:
            contentFile.write(" ".join(test_command) + "\n\r")
            contentFile.write(str(run_output_test))
        # Copy surefire/JUnit XML reports to per-mutant folder (kept for potential subsumption analysis)
        try:
            dest_dir = os.path.join(
                path.absolute(), str(mutant_id) + "-test_reports")
            os.makedirs(dest_dir, exist_ok=True)
            if buildType == "mvn":
                default_reports_dir = os.path.join(
                    source_directory, "target", "surefire-reports")
                if os.path.isdir(default_reports_dir):
                    for xml_file in Path(default_reports_dir).glob("*.xml"):
                        if xml_file.is_file():
                            shutil.copy2(str(xml_file), os.path.join(
                                dest_dir, xml_file.name))
            elif buildType == "ant":
                possible_dirs = [
                    os.path.join(source_directory, "test-results"),
                    os.path.join(source_directory, "target", "test-results"),
                    source_directory,
                ]
                for possible_dir in possible_dirs:
                    if os.path.isdir(possible_dir):
                        xml_files = list(Path(possible_dir).glob("*.xml"))
                        if xml_files:
                            for xml_file in xml_files:
                                if xml_file.is_file():
                                    shutil.copy2(str(xml_file), os.path.join(
                                        dest_dir, xml_file.name))
                            break
            elif buildType == "gradle":
                # For Gradle, reports are written directly to dest_dir via md.reportsDir
                # (similar to how Maven writes to a per-mutant directory via pom.xml configuration)
                # No copying needed - reports should already be in the correct location
                pass
        except Exception:
            # best-effort; missing reports shouldn't crash the run
            pass
        if process_test_killed or process_test_exit_code:
            if debug:
                print(f"killed: {mutation}")
            if process_test_killed:
                # Cleanup per-mutant temp build files created for parallel-safe Ant/Maven coverage runs.
                if coverage and buildType in ("mvn", "ant"):
                    tmp_build = return_build_file(" ".join(test_command))
                    try:
                        if tmp_build and os.path.isfile(tmp_build) and os.path.basename(tmp_build).endswith(str(mutant_id)):
                            os.remove(tmp_build)
                    except Exception:
                        pass
                return (mutant_id, mutation, Database.RES_ID_TIMEOUT, file, time_delta)
            # Cleanup per-mutant temp build files created for parallel-safe Ant/Maven coverage runs.
            if coverage and buildType in ("mvn", "ant"):
                tmp_build = return_build_file(" ".join(test_command))
                try:
                    if tmp_build and os.path.isfile(tmp_build) and os.path.basename(tmp_build).endswith(str(mutant_id)):
                        os.remove(tmp_build)
                except Exception:
                    pass
            return (mutant_id, mutation, Database.RES_ID_KILLED_MUTANT, file, time_delta)
        else:
            if debug:
                print(f"survived: {mutation}")
            # Cleanup per-mutant temp build files created for parallel-safe Ant/Maven coverage runs.
            if coverage and buildType in ("mvn", "ant"):
                tmp_build = return_build_file(" ".join(test_command))
                try:
                    if tmp_build and os.path.isfile(tmp_build) and os.path.basename(tmp_build).endswith(str(mutant_id)):
                        os.remove(tmp_build)
                except Exception:
                    pass
            return (mutant_id, mutation, Database.RES_ID_SURVIVED_MUTANT, file, time_delta)

    def return_class_body(self, tree):
        """
        returns ClassBodyContext nodes of the AST tree
        """
        class_bodies = []
        parents = [tree]
        for parent in parents:
            if isinstance(parent, JavaParser.ClassBodyContext) or isinstance(parent, JavaParser.InterfaceBodyContext):
                class_bodies.append(parent)
            else:
                try:
                    parents.extend(parent.getChildren())
                except AttributeError:
                    pass
        return class_bodies

    def return_body_node(self, tree):
        """
        returns ClassBodyContext nodes of the AST tree
        """
        body_id = -1
        parents = [tree]
        for parent in parents:
            if isinstance(parent, JavaParser.MethodBodyContext) or isinstance(parent, JavaParser.ConstructorBodyContext):
                body_id = parent.children[0].nodeIndex
                return body_id
            elif isinstance(parent, JavaParser.ClassBodyDeclarationContext) and (parent.getText().startswith("static{")):
                body_id = parent.children[1].nodeIndex
                return body_id
            elif isinstance(parent, JavaParser.LambdaBodyContext):
                if isinstance(parent.children[0], JavaParser.BlockContext):
                    body_id = parent.children[0].nodeIndex
                    return body_id
            else:
                try:
                    parents.append(parent.parentCtx)
                except AttributeError:
                    pass
        return body_id

    def return_method_body(self, tree, java_parse):
        """
        returns ClassBodyContext nodes of the AST tree
        """
        method_bodies = []
        parents = [tree]
        for parent in parents:
            if isinstance(parent, JavaParser.MethodBodyContext) or isinstance(parent, JavaParser.ConstructorBodyContext):
                method_bodies.append(parent.children[0])
                parents.extend(parent.children[0].getChildren())
            elif isinstance(parent, JavaParser.ClassBodyDeclarationContext) and (parent.getText().startswith("static{")):
                method_bodies.append(parent.children[1])
                parents.extend(parent.children[1].getChildren())
            elif isinstance(parent, JavaParser.LambdaBodyContext):
                # method_ = java_parse.seekFirstMatchingParent(
                #     parent, JavaParser.MethodBodyContext)
                # class_ = java_parse.seekFirstMatchingParent(
                #     parent, JavaParser.ClassBodyDeclarationContext)
                # if (method_ is None and (class_ is None or (not class_.getText().startswith("static{")))):
                if isinstance(parent.children[0], JavaParser.BlockContext):
                    method_bodies.append(parent.children[0])
            else:
                try:
                    parents.extend(parent.getChildren())
                except AttributeError:
                    pass
        return method_bodies

    @staticmethod
    def _column_from_caret(output_lines, start_line_idx, max_lookahead=12, match_end_pos=None):
        """
        Derive a 1-based column number from compiler caret formatting.

        Typical javac output:
            <code line>
                 ^
        Sometimes logs get flattened and caret may appear on the same line:
            <code line>^

        Args:
            output_lines: List of output lines
            start_line_idx: Line index where error message starts
            max_lookahead: Maximum lines to look ahead for caret
            match_end_pos: Optional position in the line where error message ends
                          (used to find the correct caret in flattened logs)
        """
        if output_lines is None:
            return None

        # First check the current line for flattened logs (caret on same line)
        if start_line_idx >= 0 and start_line_idx < len(output_lines):
            current_line = output_lines[start_line_idx]
            if "^" in current_line:
                expanded = current_line.expandtabs(8)
                # If we know where the error message ends, find caret after that position
                if match_end_pos is not None:
                    # Look for caret after the error message end position
                    search_start = match_end_pos
                    caret_pos = expanded.find("^", search_start)
                    if caret_pos >= 0:
                        return caret_pos + 1
                # Otherwise, find the rightmost caret (in case there are multiple)
                caret_pos = expanded.rfind("^")
                if caret_pos >= 0:
                    return caret_pos + 1

        end = min(len(output_lines), start_line_idx + 1 + max_lookahead)

        # Prefer "caret-only" lines: whitespace then caret.
        caret_only = re.compile(r"^[ \t]*\^")
        for j in range(start_line_idx + 1, end):
            line = output_lines[j]
            if caret_only.match(line):
                expanded = line.expandtabs(8)
                return expanded.index("^") + 1

        # Fallback: first caret occurrence in the lookahead window.
        for j in range(start_line_idx + 1, end):
            line = output_lines[j]
            if "^" in line:
                expanded = line.expandtabs(8)
                return expanded.index("^") + 1

        return None

    def find_error_ant(self, text):
        """
        Find the line and the column which causes error in Ant (Javac) output
        text: the output of the test command
        """
        # line = []
        # iter_ = re.finditer(".*\[javac\]\s+(.*\.java):(\d+):\s+error(.*)", text)
        # for m in iter_:
        #     line.append(m.end())
        ant_regex = r".*\[javac\]\s+(.*\.java):(\d+):\s+error(.*)\n.*\[javac\](.*)\n.*\[javac\](.*)\^"
        ls = re.findall(ant_regex, text)
        ls_new = []
        for l in ls:
            # l[4] is the whitespace prefix before caret in the Ant log
            col = len(l[4])
            ls_new.append([l[0], int(l[1]), int(col)])
        return ls_new

    def find_error_mvn(self, text, regex=r".*\[(\d+),(\d+)\] error:.*"):
        """
        Find file, line and column which causes error in compiler output.

        The provided regex may contain:
        - 2 groups: (file, line) and column is derived from the caret '^' line
        - 3 groups: (file, line, column)

        Column is returned as 1-based (javac-style).
        text: the output of the test command
        """
        if not text:
            return []

        pattern = re.compile(regex, re.MULTILINE)
        output_lines = text.splitlines()
        results = []

        for m in pattern.finditer(text):
            groups = m.groups()
            if len(groups) < 2:
                continue

            file_path = groups[0]
            try:
                line_no = int(groups[1])
            except Exception:
                continue

            col_no = None
            if len(groups) >= 3 and groups[2] is not None and str(groups[2]).strip() != "":
                try:
                    col_no = int(groups[2])
                except Exception:
                    col_no = None

            if col_no is None:
                output_line_idx = text[: m.start()].count("\n")
                # For flattened logs, find caret after the error message, not just any caret
                # Work directly with original text to preserve all characters
                # Find the start of the current line (last newline before match start)
                line_start_pos = text[: m.start()].rfind("\n")
                if line_start_pos == -1:
                    line_start_pos = 0
                else:
                    line_start_pos += 1  # Position after newline

                # Find the end of the current line (next newline after match, or end of text)
                line_end_pos = text.find("\n", m.end())
                if line_end_pos == -1:
                    line_end_pos = len(text)

                # Extract the full line from original text (preserving all characters)
                full_line = text[line_start_pos:line_end_pos]
                # Calculate match end position within this line
                match_end_in_line = m.end() - line_start_pos

                # Now find caret in this line after the match end position
                # Search for caret after match_end_in_line in the full_line
                caret_pos_in_line = full_line.find("^", match_end_in_line)
                if caret_pos_in_line >= 0:
                    # Convert to column number (1-based), accounting for tabs
                    expanded_line = full_line.expandtabs(8)
                    # Recalculate match_end_in_line for expanded line
                    # Count characters before match_end_in_line, expanding tabs
                    before_caret = full_line[:caret_pos_in_line]
                    expanded_before = before_caret.expandtabs(8)
                    col_no = len(expanded_before) + 1
                else:
                    # Fallback to original method if caret not found on same line
                    col_no = Schemata._column_from_caret(
                        output_lines, output_line_idx, match_end_pos=None)

            if col_no is None:
                continue

            results.append([file_path, line_no, int(col_no)])

        # De-duplicate while preserving order
        seen = set()
        uniq = []
        for r in results:
            key = (r[0], r[1], r[2])
            if key not in seen:
                seen.add(key)
                uniq.append(r)
        return uniq

    def _insert_initial_tests_into_db(self, build_directory, buildType, mutation_db: Database):
        """Parse initial run test reports and insert test records into the DB (id auto-increment)."""
        reports = []
        if buildType == "mvn":
            default_reports_dir = os.path.join(
                build_directory, "target", "surefire-reports")
            if os.path.isdir(default_reports_dir):
                reports = list(Path(default_reports_dir).glob("*.xml"))
        elif buildType == "ant":
            for possible_dir in [
                os.path.join(build_directory, "test-results"),
                os.path.join(build_directory, "target", "test-results"),
                build_directory,
            ]:
                if os.path.isdir(possible_dir):
                    candidates = list(Path(possible_dir).glob("*.xml"))
                    if candidates:
                        reports = candidates
                        break
        elif buildType == "gradle":
            reports = list(Path(build_directory).glob(
                "**/build/test-results/**/*.xml"))

        if not reports:
            return

        # Existing test names
        existing = set([row[1] for row in mutation_db.fetch_data("test")])

        # Parse and insert
        for xml_path in reports:
            try:
                results = parse_junit_xml(str(xml_path))
            except Exception:
                continue
            for res in results:
                test_name = res[0]
                if test_name and test_name not in existing:
                    mutation_db.insert_data(
                        "test", "qualified_name", [test_name])
                    existing.add(test_name)

    def mutant_schemata_generation(
        self,
        options,
        filterType,
        filterList,
        mutation_database,
        debug=True
    ):
        if mutation_database is None:
            print("Error opening databases.")
            return
        build_command = getCommand(options.buildCommand)
        enabledMutators = "Traditional"

        if options.isNullCheck:
            enabledMutators = "Null"
        if options.isAll:
            enabledMutators = "All"
        if options.isMethodLevel:
            enabledMutators = "Method"

        java_io = JavaIO(options.isVerboseActive)

        try:
            assert os.path.isdir(options.sourcePath)
        except AssertionError as exception:
            print("Source path must be a directory.")
            sys.exit(1)

        # Parsing the source file into a tree.
        java_io.listFiles(
            targetPath=os.path.abspath(options.sourcePath),
            buildPath=os.path.abspath(options.buildPath),
            filterType=filterType,
            filterList=filterList,
        )

        fileCounter = 0
        fileCount = len(java_io.fileList)

        # refreshing the database
        mutation_database.delete_data("mutant")
        mutation_database.delete_data("mutation")

        densityResultsPath = os.path.join(
            java_io.targetDirectory, "ProjectDensityReport.csv"
        )
        print("Source Path: ", java_io.sourceDirectory)
        print("Target Path: ", java_io.targetDirectory)
        print("Creating Mutation Database: ", self.sqlDBPath)

        file_mutations_dict = {}
        compile_mutations_files = set()

        build_failures = set()
        mutantTypes_project = dict()
        trees_dict = dict()
        last_mutation_id = 0

        for file in java_io.fileList:
            print(
                "\n(" + str(fileCounter + 1) + "/" +
                str(fileCount) + ") Source file: ",
                file,
            )

            file_mutations_dict[file] = dict()

            # Normalize file path to match database format (relative path)
            normalized_file = normalize_file_path(file, options.buildPath)
            file_results = mutation_database.fetch_data(
                "file", columns="id", condition=f"name = '{normalized_file}'"
            )
            if not file_results:
                # Try with original file path in case it wasn't normalized when inserted
                file_results = mutation_database.fetch_data(
                    "file", columns="id", condition=f"name = '{file}'"
                )
            if not file_results:
                raise ValueError(
                    f"File not found in database: {file} (normalized: {normalized_file})")
            file_id = file_results[0][0]

            try:
                # parsing the source file into a tree.
                java_parse = JavaParse(options.isVerboseActive)
                source_code = java_io.getFileContent(file)
                tree = java_parse.parse(source_code)
            except Exception as e:
                print("Error in parsing Java code, skipping the file.")
                sys.stderr.write(str(e))
                continue
            fileCounter += 1

            # -----------------------------------------------------
            # Normalize file path to match database format and create class folder structure
            normalized_file = normalize_file_path(file, options.sourcePath)
            # Use the normalized file path directly (keeping .java extension)
            targetDir = os.path.join(
                self.LittleDarwinResultsPath, normalized_file)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir, exist_ok=True)
            if not os.path.isfile(os.path.join(targetDir, "original.java")):
                shutil.copyfile(file, os.path.join(targetDir, "original.java"))
            # -----------------------------------------------------
            mutantsPerLine = dict()
            mutantsPerMethod = dict()
            mutationOperators = list()

            # ? for debugging purposes
            if (debug):
                json_ = java_parse.tree2JSON_DFS(tree)
                f = open(
                    os.path.join(self.LittleDarwinResultsPath,
                                 os.path.basename(file) + "-tree.json"), "w")
                f.write(json_)
                f.close()
                java8_mutate_test = JavaMutate(
                    sourceTree=tree,
                    sourceCode=source_code,
                    javaParseObject=java_parse,
                    file_name=file,
                    verbose=True,
                    mutantTypes=[enabledMutators]
                )
                mutantTypes = java8_mutate_test.gatherMutations(
                    metaTypes=[enabledMutators],
                )
                print("--> TEST Mutations found: ", sum(mutantTypes.values()))
                for mutantType in mutantTypes.keys():
                    if mutantTypes[mutantType] > 0:
                        print("---->", mutantType, ":",
                              mutantTypes[mutantType])
                print("-------------------------------------")

            mutantTypes_file = dict()

            java8_mutate = JavaMutate(
                sourceTree=tree,
                sourceCode=source_code,
                javaParseObject=java_parse,
                file_name=file,
                verbose=options.isVerboseActive,
                metaTypes=[enabledMutators]
            )
            # gather all the nodes that can be mutated
            (node_dict, depth_node, overloaded) = java8_mutate.gatherMutableNodes(
                javaParseObject=java_parse,
                metaTypes=[enabledMutators], mutationOperator=MutationOperator)
            # sort the nodes by depth so that we can mutate them from bottom to top
            depths = list(depth_node.keys())
            depths.sort(reverse=True)

            for node_depth in depths:
                depth_node[node_depth] = list(depth_node[node_depth])
                for nodeInd in depth_node[node_depth]:
                    # get the node to be mutated
                    main_node = java_parse.getNode(tree, nodeInd)
                    body_ind = self.return_body_node(main_node)
                    # ? for debugging purposes
                    if (debug):
                        print("nodeIndex: "+str(nodeInd))
                    node_dict[nodeInd] = sorted(
                        node_dict[nodeInd], key=lambda x: str(type(x)).lower(), reverse=False)
                    for mO in node_dict[nodeInd]:
                        mO.mutation_id = last_mutation_id
                        mO.generateMutations()
                        precedence_ordered_mutations = list()
                        # In LogicalOperatorReplacement and ConditionalOperatorReplacement we need to generate all possible combinations as they change the precedence
                        if (isinstance(mO, LogicalOperatorReplacement) or isinstance(mO, ConditionalOperatorReplacement)):
                            precedence_ordered_mutations = java8_mutate.all_mutations_pairs(
                                order=len(mO.mutations), mutations=mO.mutations)
                        mutantTypes_project[mO.mutatorType] = len(mO.mutations) if not mO.mutatorType in mutantTypes_project.keys(
                        ) else mutantTypes_project[mO.mutatorType]+len(mO.mutations)

                        mutantTypes_file[mO.mutatorType] = len(mO.mutations) if not mO.mutatorType in mutantTypes_file.keys(
                        ) else mutantTypes_file[mO.mutatorType]+len(mO.mutations)
                        if (precedence_ordered_mutations):
                            is_overloaded = False
                            for mutation in mO.mutations:
                                if nodeInd in overloaded:
                                    is_overloaded = True
                                    compile_mutations_files.add(
                                        (file, mutation))
                                    mutationIDs_tmp = JavaParse.findNodeInSubtree(tree, mutation.nodeID).mutationID if hasattr(
                                        JavaParse.findNodeInSubtree(tree, mutation.nodeID), "mutationID") else ""
                                    mutationIDs_tmp += "," + \
                                        str(mutation.mutationID) if (
                                            mutationIDs_tmp != "") else str(mutation.mutationID)
                                    JavaParse.findNodeInSubtree(
                                        tree, mutation.nodeID).mutationID = mutationIDs_tmp
                                operator_id = mutation_database.fetch_data(
                                    "mutation_operator",
                                    "id",
                                    f"name = '{mutation.mutatorType}'",
                                )
                                operator_id = operator_id[0][0]

                                new_node_jsons = []
                                new_node_ids = []
                                new_node_types = []
                                for i in range(len(mutation.mutation_dict[mutation.mutationID][0])):
                                    new_node_ids.append(
                                        mutation.mutation_dict[mutation.mutationID][0][i])
                                    new_node_jsons.append(
                                        java_parse.tree2JSON_DFS(mutation.mutation_dict[mutation.mutationID][1][i]))
                                    new_node_types.append(
                                        mutation.mutation_dict[mutation.mutationID][2][i])

                                mutation_database.insert_mutation(
                                    mutation.mutationID,
                                    file_id,
                                    mutation.nodeID,
                                    mutation.startPos,
                                    mutation.endPos,
                                    mutation.lineNumber,
                                    mutation.replacementText,
                                    mutation_operator_id=operator_id,
                                    node_json=new_node_jsons,
                                    new_node_id=new_node_ids,
                                    new_node_type=new_node_types,
                                    is_compile_time=1 if is_overloaded else 0,
                                    object_=dill.dumps(
                                        mutation) if is_overloaded else None
                                )
                                # mutations_in_node[tuple_str].mutationID = tuple_str
                                file_mutations_dict[file][mutation.mutationID] = mutation
                                last_mutation_id += 1
                                if mutation.lineNumber in mutantsPerLine.keys():
                                    mutantsPerLine[mutation.lineNumber] += 1
                                else:
                                    mutantsPerLine[mutation.lineNumber] = 1
                            if is_overloaded:
                                continue
                            mutations_in_node = dict()
                            # -1: the original node
                            mutations_in_node["-1"] = recursiveCloneANTLRNodeAndItsChildren(
                                main_node)
                            for mutation_order in precedence_ordered_mutations:
                                for mutation_tuples in mutation_order:
                                    hom = HOM(list(mutation_tuples))
                                    tuple_str = ""
                                    # I use this so that when I generate higher order mutants I replace them in the same tree
                                    for mutation_ind in range(len(mutation_tuples)):
                                        mutation = mutation_tuples[mutation_ind]
                                        operator_id = mutation_database.fetch_data(
                                            "mutation_operator",
                                            "id",
                                            f"name = '{mutation.mutatorType}'",
                                        )
                                        operator_id = operator_id[0][0]

                                        tuple_str += "," + \
                                            str(mutation.mutationID) if (
                                                tuple_str != "") else str(mutation.mutationID)
                                    mutations_in_node[tuple_str] = recursiveCloneANTLRNodeAndItsChildren(
                                        hom.return_mutated_node(main_node, list(mutation_tuples)))
                                    hom.return_original_node(
                                        main_node, list(mutation_tuples))
                                    mutations_in_node[tuple_str].mutationID = tuple_str
                                    mutations_in_node[tuple_str].hom = hom
                            tmp = java8_mutate.returnTernary(
                                mutations_in_node, main_node.mutationType if hasattr(main_node, "mutationType") else 0, body_ind)
                            # ? for debugging purposes
                            if (debug):
                                print("final expression: " +
                                      tmp.getText())
                            tmp.parentCtx = main_node.parentCtx
                            replaceNodes(main_node, tmp)
                        else:
                            for mutation in mO.mutations:
                                # getting the pointer to the node to be mutated
                                # we need the expression after the return keyword (example: return x)
                                if mutation.mutatorType == "NullifyReturnValue":
                                    replaced_node = JavaParse.findNodeInSubtree(tree, JavaParse.findNodeInSubtree(
                                        tree, mutation.nodeID).getChild(1).nodeIndex)
                                elif mutation.mutatorType == "NullifyInputVariable":  # we need the block of the method
                                    replaced_node = JavaParse.findNodeInSubtree(tree, JavaParse.findNodeInSubtree(
                                        tree, mutation.nodeID).methodBody().block().nodeIndex)
                                else:  # all other cases
                                    replaced_node = JavaParse.findNodeInSubtree(
                                        tree, mutation.nodeID)
                                body_ind = self.return_body_node(replaced_node)
                                # ? for debugging purposes
                                if (debug):
                                    print(
                                        "type: "+str(type(replaced_node)))
                                    print("mutation type: " +
                                          mutation.mutatorType)

                                operator_id = mutation_database.fetch_data(
                                    "mutation_operator",
                                    "id",
                                    f"name = '{mutation.mutatorType}'",
                                )
                                operator_id = operator_id[0][0]

                                new_node_jsons = []
                                new_node_ids = []
                                new_node_types = []
                                for i in range(len(mutation.mutation_dict[mutation.mutationID][0])):
                                    new_node_ids.append(
                                        mutation.mutation_dict[mutation.mutationID][0][i])
                                    new_node_jsons.append(
                                        java_parse.tree2JSON_DFS(mutation.mutation_dict[mutation.mutationID][1][i]))
                                    new_node_types.append(
                                        mutation.mutation_dict[mutation.mutationID][2][i])

                                mutation_database.insert_mutation(
                                    mutation.mutationID,
                                    file_id,
                                    mutation.nodeID,
                                    mutation.startPos,
                                    mutation.endPos,
                                    mutation.lineNumber,
                                    mutation.replacementText,
                                    mutation_operator_id=operator_id,
                                    node_json=new_node_jsons,
                                    new_node_id=new_node_ids,
                                    new_node_type=new_node_types,
                                    is_compile_time=1 if ((hasattr(replaced_node, "mutationType") and replaced_node.mutationType ==
                                                          JavaParse.MUTATION_TYPE_COMPILE_TIME) or mutation.nodeID in overloaded) else 0,
                                    object_=dill.dumps(mutation) if ((hasattr(replaced_node, "mutationType") and replaced_node.mutationType ==
                                                                      JavaParse.MUTATION_TYPE_COMPILE_TIME) or mutation.nodeID in overloaded) else None
                                )

                                file_mutations_dict[file][mutation.mutationID] = mutation

                                last_mutation_id += 1
                                if mutation.lineNumber in mutantsPerLine.keys():
                                    mutantsPerLine[mutation.lineNumber] += 1
                                else:
                                    mutantsPerLine[mutation.lineNumber] = 1

                                mutations_in_node = dict()
                                skipTernary = False

                                # -1: the original node
                                mutations_in_node["-1"] = recursiveCloneANTLRNodeAndItsChildren(
                                    replaced_node)
                                # Compile time mutations are not ternary
                                if (hasattr(replaced_node, "mutationType") and replaced_node.mutationType == JavaParse.MUTATION_TYPE_COMPILE_TIME) or mutation.nodeID in overloaded:
                                    compile_mutations_files.add(
                                        (file, mutation))
                                else:
                                    mutation.apply_mutation_in_place(
                                        replaced_node)
                                # copy the mutated expression
                                copiedParent = recursiveCloneANTLRNodeAndItsChildren(
                                    replaced_node)

                                tuple_str = copiedParent.mutationID if hasattr(
                                    copiedParent, "mutationID") else ""
                                tuple_str += "," + \
                                    str(mutation.mutationID) if (
                                        tuple_str != "") else str(mutation.mutationID)
                                # copiedParent.mutationID = mutation.mutationID
                                copiedParent.mutationID = tuple_str
                                mutations_in_node[tuple_str] = copiedParent
                                if (hasattr(replaced_node, "mutationType") and replaced_node.mutationType == JavaParse.MUTATION_TYPE_COMPILE_TIME) or mutation.nodeID in overloaded:
                                    skipTernary = True
                                else:
                                    # reverse mutate after copying the parent
                                    mutation.apply_reverse_mutation_in_place(
                                        replaced_node)
                                # ? for debugging purposes
                                if (debug):
                                    print("original_Version: " +
                                          replaced_node.getText())
                                    print("mutated_Version: " +
                                          copiedParent.getText())
                                #! **********************************************
                                if (skipTernary):
                                    tmp = copiedParent
                                else:
                                    # For RemoveMethod and NullifyInputVariable we use if instead of ternary
                                    if (mutation.mutatorType == "RemoveMethod" or mutation.mutatorType == "NullifyInputVariable"):
                                        blockContext = JavaParser.BlockContext(
                                            replaced_node)
                                        bracet1 = TerminalNodeImpl(Token())
                                        bracet1.symbol.text = "{"
                                        blockContext.addChild(bracet1)
                                        temp = JavaMutate.returnConditional(
                                            mutationID=mutation.mutationID, node=copiedParent, original_nodeIndex=JavaMutate.return_class_id(replaced_node), contextID=replaced_node.contextID)
                                        blockContext.addChild(temp)
                                        for ind in range(len(replaced_node.children)):
                                            if ind != 0 and ind != (len(replaced_node.children)-1):
                                                blockContext.addChild(
                                                    replaced_node.children[ind])
                                        bracet2 = TerminalNodeImpl(Token())
                                        bracet2.symbol.text = "}"
                                        blockContext.addChild(bracet2)
                                        tmp = blockContext
                                    else:
                                        tmp = java8_mutate.returnTernary(
                                            mutations_in_node, replaced_node.mutationType if hasattr(replaced_node, "mutationType") else 0, body_ind)
                                # ************************************************************************************************
                                # ? for debugging purposes
                                if (debug):
                                    print("final expression: "+tmp.getText())
                                # tmp.mutationID = mutation.mutationID
                                tmp.parentCtx = replaced_node.parentCtx
                                replaceNodes(replaced_node, tmp)

            print("--> Mutations found: ", sum(mutantTypes_file.values()))
            for mutantType in mutantTypes_file.keys():
                if mutantTypes_file[mutantType] > 0:
                    print("---->", mutantType, ":",
                          mutantTypes_file[mutantType])
            print("-------------------------------------")
            # adding getEnv and ld variables to methods
            class_bodies = self.return_class_body(tree)
            for class_body in class_bodies:
                if (class_body.contextID == JavaParse.CLASS_BODY_CONTEXT_ID):
                    JavaMutate.add_getEnv(class_body)
            method_bodies = self.return_method_body(tree, java_parse)
            for method_body in method_bodies:
                blockContext = JavaMutate.add_ld_variable(
                    method_body)
                blockContext.parentCtx = method_body.parentCtx
                replaceNodes(method_body, blockContext)

            # saving the file
            with open(file, "w",) as f:
                # the last node is <EOF>
                del tree.children[-1]
                f.write(java_parse.getText(tree))

            # report generation
            java8_mutate.mutationOperators = list(mutationOperators)
            densityReport = java8_mutate.aggregateReport_schemata(
                self.littleDarwinVersion, file_mutations_dict[file].values(
                ), mutantsPerLine
            )

            aggregateComplexity = java_io.getAggregateComplexityReport(
                mutantsPerMethod,
                java_parse.getCyclomaticComplexityAllMethods(tree),
                java_parse.getLinesOfCodePerMethod(tree),
            )

            if (
                mutantsPerLine is not None
                and densityReport is not None
                and aggregateComplexity is not None
            ):
                densityPerLineCSVFile = os.path.abspath(
                    os.path.join(targetDir, "MutantDensityPerLine.csv")
                )
                complexityPerMethodCSVFile = os.path.abspath(
                    os.path.join(targetDir, "ComplexityPerMethod.csv")
                )
                densityReportFile = os.path.abspath(
                    os.path.join(targetDir, "aggregate.html")
                )

            if (
                not os.path.isfile(complexityPerMethodCSVFile)
                or not os.path.isfile(densityPerLineCSVFile)
                or not os.path.isfile(densityReportFile)
            ):
                with open(densityPerLineCSVFile, "w") as densityFileHandle:
                    for key in sorted(mutantsPerLine.keys()):
                        densityFileHandle.write(
                            str(key) + "," + str(mutantsPerLine[key]) + "\n"
                        )

                with open(complexityPerMethodCSVFile, "w") as densityFileHandle:
                    for key in sorted(aggregateComplexity.keys()):
                        line = [str(key)]
                        line.extend([str(x) for x in aggregateComplexity[key]])
                        densityFileHandle.write(";".join(line) + "\n")

                with open(densityReportFile, "w") as densityFileHandle:
                    densityFileHandle.write(densityReport)
            trees_dict[os.path.abspath(file)] = tree

        # removing build failure causing mutations
        # running the build command
        while True:
            (
                process_build_killed,
                process_build_exit_code,
                run_output_build,
                time_delta
            ) = timeoutAlternative(
                build_command.copy(),
                workingDirectory=os.path.abspath(options.buildPath),
                timeout=int(options.timeout),
                failMessage=options.fail_string,
            )
            if not process_build_killed and not process_build_exit_code:
                break  # if the build command succeeds
            if debug:
                print("build failure:")
                print(run_output_build)
            # if the build command fails, find the line and the column that causes error
            ls_new = list()
            # find the line and the column that causes error
            if build_command[0] == "ant":
                ls_new = self.find_error_ant(run_output_build)
            # elif build_command[0] == "mvn":
            else:
                ls_new = self.find_error_mvn(
                    run_output_build, options.compile_failure_regex)
            # ls_new.sort()
            if (ls_new == []):
                print(
                    "Schemata compilation failed but the line and the column are not detected. You might want to check the regex. The output is saved to failure_output.txt")
                with open(os.path.abspath(
                    os.path.join(
                        options.buildPath, "LittleDarwinResults", "failure_output.txt"
                    )
                ), "w") as contentFile:
                    contentFile.write(str(run_output_build))
                sys.exit(3)
            matches = set()
            for l in ls_new:
                source_code = java_io.getFileContent(l[0])
                lines = source_code.split('\n')
                row = l[1]-1
                column = l[2]-1
                startPos = column-7
                endPos = column+2
                # Search for the mutation ID
                match = re.search(r"MUT(\d+)\s*\*/",
                                  lines[row][startPos:endPos])
                # If there is no match re-index the start position and try again
                while match is None:
                    startPos -= 1
                    if (startPos < 0):
                        if (row == 0):
                            print("ERROR in detecting the mutant ID!")
                            with open(os.path.abspath(
                                os.path.join(
                                    options.buildPath, "LittleDarwinResults", "failure_output.txt"
                                )
                            ), "w") as contentFile:
                                contentFile.write(str(run_output_build))
                            raise subprocess.CalledProcessError(3,
                                                                self.options.buildCommand.split(
                                                                    ",") if self.options.initialBuildCommand == "***dummy***" else getCommand(self.options.initialBuildCommand),
                                                                run_output_build,
                                                                )
                        else:
                            row = row - 1
                            column = len(lines[row])
                            startPos = column - 7
                            endPos = column
                    match = re.search(
                        r"MUT(\d+)\s*\*/", lines[row][startPos:endPos]
                    )
                matches.add((l[0], int(match.group(1))))
                startPos = startPos - 2
            for match in matches:
                print(str(match[1]), end="-")
                build_failures.add(match[1])
                # Normalize file path to match database format and create class folder structure
                normalized_file = normalize_file_path(
                    match[0], options.sourcePath)
                # Use the normalized file path directly (keeping .java extension)
                targetDir = os.path.join(
                    self.LittleDarwinResultsPath, normalized_file)
                if not os.path.exists(targetDir):
                    os.makedirs(targetDir, exist_ok=True)
                targetTextOutputFile = os.path.join(
                    targetDir, str(match[1]) + ".txt")
                with open(targetTextOutputFile, "w") as contentFile:
                    contentFile.write(" ".join(build_command) + "\n\r")
                    contentFile.write(str(run_output_build))
                # find the nodes that have the mutation
                tree = 0
                nodes_ = findNodesWithMutationID(
                    trees_dict[os.path.abspath(match[0])], str(match[1]))
                if debug:
                    for node_ in nodes_:
                        print(node_.getText())
                for node_ in nodes_:
                    if (hasattr(node_, "hom")):
                        # if its a hom node, reverse mutate the mutation which caused the build failure
                        node_.hom.return_original_node(mutated_tree=node_, mutationList=[
                                                       file_mutations_dict[os.path.abspath(match[0])][match[1]]])
                        mutationIDs = str(node_.mutationID).split(",")
                        mutationIDs_ = ""
                        for child_mutationID in mutationIDs:
                            if (child_mutationID == str(match[1])):
                                mutationIDs_ += str(match[1]) + \
                                    "," if mutationIDs_ != "" else str(
                                        match[1])
                        node_.mutationID = mutationIDs_
                    else:
                        # if its a FOM node, reverse mutate the mutation
                        file_mutations_dict[os.path.abspath(match[0])][match[1]].apply_reverse_mutation_in_place(
                            mutated_tree=node_)
                # ? for debugging purposes
                if (debug):
                    print(
                        repr(l)
                        + " : "
                        + str(match[1])
                    )
            # write the schemata file without the build failure causing mutations
            for match in matches:
                with open(
                    match[0],
                    "w",
                ) as f:
                    f.write(java_parse.getText(
                        trees_dict[os.path.abspath(match[0])]))

        for file in java_io.fileList:
            # Normalize file path to match database format and create class folder structure
            normalized_file = normalize_file_path(file, options.sourcePath)
            # Use the normalized file path directly (keeping .java extension)
            targetDir = os.path.join(
                self.LittleDarwinResultsPath, normalized_file)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir, exist_ok=True)
            shutil.copyfile(file, os.path.join(
                targetDir, "mutant_schemata.java"))
            self._format_java_file(os.path.join(
                targetDir, "mutant_schemata.java"))

            if not os.path.abspath(file) in trees_dict.keys():
                continue
            json_string = java_parse.tree2JSON_DFS(
                trees_dict[os.path.abspath(file)])
            # Normalize file path to relative path from project root before updating
            mutation_database.update_file_json(
                file, json_string, options=options)
            shutil.copyfile(os.path.join(targetDir, "original.java"), file)

        print("-------------------------------------")
        print("\nTotal mutations found: ", sum(mutantTypes_project.values()))
        print("Build failure causing mutations found: ", len(build_failures))
        print("Compile time mutations found: ", len(compile_mutations_files))
        for mutantType in mutantTypes_project.keys():
            if mutantTypes_project[mutantType] > 0:
                print("---->", mutantType, ":",
                      mutantTypes_project[mutantType])
        print("-------------------------------------")
        return (
            build_failures,
            file_mutations_dict
        )

    def print_results(self, res_dict, start_time):

        fileCounter = 0
        totalMutantCount = 0
        totalMutantCounter = 0

        for file in res_dict.keys():
            totalMutantCount += len(res_dict[file]["mutantsList"])
            tmp = set.union(set(res_dict[file]["survivedList"]), set(res_dict[file]["killedList"]), set(res_dict[file]["timeoutList"]), set(
                res_dict[file]["nonCoveredList"]), set(res_dict[file]["buildFailureList"]), set(res_dict[file]["testFailureList"]))
            totalMutantCounter += len(tmp)

        # When using mutationIdsFile, use HOM definition count instead of total mutants across files
        if hasattr(self, 'hom_definitions_count') and self.hom_definitions_count is not None:
            totalMutantCount = self.hom_definitions_count

        line_no = 0
        mvaddstr(line_no, 0, " total: " + str(totalMutantCounter) + "/" + str((totalMutantCount)) + " elapsed: " +
                 str(datetime.timedelta(seconds=int(time.time() - start_time))) + " remaining: " + str(
                     datetime.timedelta(
                         seconds=int(
                                    (float(time.time() - start_time) /
                                     (totalMutantCounter if totalMutantCounter != 0 else 1))
                             * float(totalMutantCount - totalMutantCounter)
                         )
                     )
        ))

        line_no += 1
        for file in res_dict.keys():
            fileCounter += 1
            tmp = set.union(set(res_dict[file]["survivedList"]), set(res_dict[file]["killedList"]), set(res_dict[file]["timeoutList"]), set(
                res_dict[file]["nonCoveredList"]), set(res_dict[file]["buildFailureList"]), set(res_dict[file]["testFailureList"]))
            current = len(tmp)
            if (current == len(res_dict[file]["mutantsList"])):
                mvdeleteln(line_no, 0)
                mvdeleteln(line_no+1, 0)
                continue
            mvaddstr(line_no, 0, " (" + str(fileCounter) + "/" + str(len(res_dict)) +
                     ") collecting results for "+file)
            line_no += 1
            mvaddstr(line_no, 0, " current: " + str(current) + "/" +
                     str(len(res_dict[file]["mutantsList"])) + " *** survived: " + str(len(res_dict[file]["survivedList"])) +
                     " - killed: " + str(len(res_dict[file]["killedList"])) + " - non-covered: " + str(
                len(res_dict[file]["nonCoveredList"])))
            line_no += 1

    def run_mutant_schemata(
        self,
        mutants_dict,
        # build_failures,
        compile_mutations_files,
        mutation_db: Database,
        options,
        debug=False
    ):

        start_time = time.time()
        res_dict = dict()

        JOBS_NO = options.numberOfJobs
        build_command = getCommand(options.buildCommand)
        clean_command = getCommand(options.cleanUp)
        test_command = getCommand(options.testCommand)

        source_directory = os.path.abspath(options.sourcePath)
        build_directory = os.path.abspath(options.buildPath)
        # Allow passing a build file path (e.g., pom.xml) instead of a directory.
        if os.path.isfile(build_directory):
            build_directory = os.path.dirname(build_directory)

        buildType = ""
        buildType = detect_build_tool(build_command[0])
        buildFile = return_build_file(" ".join(build_command))
        if buildFile == None:
            if buildType == "ant":
                buildFile = os.path.join(build_directory, "build.xml")
            elif buildType == "mvn":
                buildFile = os.path.join(build_directory, "pom.xml")
            elif buildType == "gradle":
                groovy = os.path.join(build_directory, "build.gradle")
                kotlin = os.path.join(build_directory, "build.gradle.kts")
                buildFile = groovy if os.path.isfile(groovy) else (
                    kotlin if os.path.isfile(kotlin) else groovy)

        # let's tell the user upfront that this may corrupt the source code.
        print("\n\n!!! CAUTION !!!")
        print("Code can be changed accidentally. Create a backup first.\n")

        if options.alternateDb == "***dummy***":
            databasePath = os.path.abspath(
                os.path.join(
                    options.buildPath, "LittleDarwinResults", "mutationdatabase"
                )
            )
        else:
            databasePath = options.alternateDb

        mutantsPath = os.path.dirname(databasePath)
        assert os.path.isdir(mutantsPath)

        java_parse = JavaParse(options.isVerboseActive)
        java_io = JavaIO(options.isVerboseActive)
        java_io.listFiles(
            targetPath=os.path.abspath(source_directory),
            buildPath=os.path.abspath(build_directory),
        )
        function_calls = list()

        # moving schemata to the main directory
        for file in java_io.fileList:
            targetDir = os.path.join(
                self.LittleDarwinResultsPath,
                os.path.relpath(file, options.sourcePath),
            )
            if os.path.isfile(os.path.join(targetDir, "mutant_schemata.java")):
                shutil.copyfile(os.path.join(
                    targetDir, "mutant_schemata.java"), file)
        if not options.isCoverageActive:
            # Determine initial command: always try to run test command if available to get surefire reports
            # This ensures test discovery regardless of subsumption being active

            if options.cleanUp != "***dummy***":
                s_time = time.time()
                (
                    process_clean_killed,
                    process_clean_exit_code,
                    run_output_clean,
                    time_delta
                ) = timeoutAlternative(
                    clean_command,
                    workingDirectory=build_directory,
                    timeout=int(options.timeout),
                    failMessage=options.fail_string,
                )
                self.clean_time += time.time() - s_time
            if options.buildCommand != "***dummy***":
                (
                    process_build_killed,
                    process_build_exit_code,
                    run_output_build,
                    time_delta
                ) = timeoutAlternative(
                    build_command,
                    workingDirectory=build_directory,
                    timeout=int(options.initial_timeout),
                    failMessage=options.fail_string,
                )

            if options.testCommand != "***dummy***":
                initial_command = test_command.copy()
            else:
                # Fall back to build command if test command not specified
                initial_command = options.buildCommand.split(
                    ",") if options.initialBuildCommand == "***dummy***" else getCommand(options.initialBuildCommand)
            (
                process_build_killed,
                process_build_exit_code,
                run_output_build,
                time_delta
            ) = timeoutAlternative(
                initial_command,
                workingDirectory=build_directory,
                timeout=int(options.initial_timeout),
                failMessage=options.fail_string,
            )
            # After initial build/test, always parse surefire XMLs and ensure tests are recorded in DB
            # This keeps test records available for subsumption analysis when needed
            try:
                self._insert_initial_tests_into_db(
                    build_directory, buildType, mutation_db)
            except Exception:
                pass
        print("Running mutants...", end=' ')
        compile_mutations_trees = dict()
        compile_mutations_ = dict()
        if len(compile_mutations_files) > 0:
            print("Running compile time mutants...", end=' ')
            for CTM in compile_mutations_files:
                # Convert sourcePath-relative path back to buildPath-relative for DB lookup
                normalized_ctm_file = source_relative_to_build_relative(
                    CTM[0], options.sourcePath, options.buildPath)
                output = mutation_db.fetch_data(
                    "file", "*", f"name = '{normalized_ctm_file}'")
                # If not found with normalized path, try original
                if not output:
                    output = mutation_db.fetch_data(
                        "file", "*", f"name = '{CTM[0]}'")
                if not output:
                    print(
                        f"Warning: File not found in database: {CTM[0]} (normalized: {normalized_ctm_file})")
                    continue
                # source_code = java_io.getFileContent(CTM[0])
                # tree = java_parse.parse(source_code)
                if (CTM[0] in compile_mutations_trees.keys()):
                    continue
                tree = java_parse.Json2Tree(output[0][2])
                compile_mutations_trees[CTM[0]] = tree
            for CTM in compile_mutations_files:
                tree = compile_mutations_trees[CTM[0]]
                expressionContexts = findNodesWithMutationID(
                    tree, str(CTM[1].mutationID))
                compile_mutations_[CTM[1].mutationID] = list()
                for expression in expressionContexts:
                    compile_mutations_[CTM[1].mutationID].append([
                        CTM[1], expression])
        build_failure_mutants = mutation_db.fetch_build_failure_mutants(
            options=options)
        for file in mutants_dict.keys():
            # file is the relative path from the source path
            # Create subdirectory for this class in LittleDarwinResults (keeping .java extension)
            targetDir = os.path.join(self.LittleDarwinResultsPath, file)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir, exist_ok=True)
            res_dict[file] = {"mutantsList": list(mutants_dict[file].keys()), "survivedList": list(), "killedList": list(
            ), "nonCoveredList": list(), "buildFailureList": list(), "testFailureList": list(), "timeoutList": list()}
            #! antomology has problem with build failures. It reports them both as killed at build and survived
            for record in build_failure_mutants:
                if (record[0] == file):
                    mutant_id_str = str(record[1])
                    if mutant_id_str not in res_dict[record[0]]["killedList"]:
                        res_dict[record[0]]["killedList"].append(mutant_id_str)
                    if mutant_id_str not in res_dict[record[0]]["buildFailureList"]:
                        res_dict[record[0]]["buildFailureList"].append(
                            mutant_id_str)
            for mutant_id in mutants_dict[file].keys():
                if str(mutant_id) in res_dict[file]["buildFailureList"]:
                    continue
                subset = mutants_dict[file][mutant_id]
                compile_again = list()
                for mutation in subset:
                    # if the mutant is in the compile mutations list then compile and run it again
                    if mutation in compile_mutations_.keys():
                        compile_again.append(mutation)
                        for i in range(len(compile_mutations_[mutation])):
                            (app_inds, app_nodes) = compile_mutations_[mutation][i][0].apply_mutation_in_place(
                                compile_mutations_[mutation][i][1]
                            )
                            compile_mutations_[mutation][i] = [
                                compile_mutations_[mutation][i][0], compile_mutations_[mutation][i][1], app_inds, app_nodes]
                        # compile_mutations_[mutation][0].apply_mutation_in_place(
                        #     compile_mutations_[mutation][1])
                if len(compile_again) != 0:
                    print(subset, end=" ")
                    # run mutations that need recompilation
                    for c_a in compile_again:
                        with open(
                            file,
                            "w",
                        ) as f:
                            f.write(
                                java_parse.getText(
                                    compile_mutations_trees[file]
                                )
                            )
                        self._format_java_file(file)
                    if options.cleanUp != "***dummy***":
                        s_time = time.time()
                        (
                            process_clean_killed,
                            process_clean_exit_code,
                            run_output_clean,
                            time_delta
                        ) = timeoutAlternative(
                            clean_command,
                            workingDirectory=build_directory,
                            timeout=int(options.timeout),
                            failMessage=options.fail_string,
                        )
                        self.clean_time += time.time() - s_time
                    os.makedirs(
                        os.path.join(
                            targetDir,
                            str(mutant_id) + "-test_reports",
                        ),
                        exist_ok=True,
                    )
                    no_test = False
                    buildFile_ = buildFile
                    if options.isCoverageActive:
                        if (buildType == "mvn"):
                            D_args = return_D_arguments(" ".join(test_command))
                        lines = mutation_db.fetch_file_mutant_by_mutation_ID(
                            mutant_id, options=options)
                        test_names = list()
                        for line in lines:
                            test_names.extend(
                                mutation_db.fetch_coverage(file, line[2], options=options))
                        # insturmented but not covered
                        non_covered = False
                        while ("-",) in test_names:
                            non_covered = True
                            test_names.remove(("-",))
                        if non_covered:
                            if len(test_names) == 0:
                                res = (mutant_id, subset,
                                       Database.RES_ID_NON_COVERED, file)
                                msg = "non-covered"
                                mutant_id_str = str(res[0])
                                if mutant_id_str not in res_dict[res[3]]["nonCoveredList"]:
                                    res_dict[res[3]]["nonCoveredList"].append(
                                        mutant_id_str)
                                continue
                        no_test = False
                        while ("?",) in test_names:
                            no_test = True
                            test_names.remove(("?",))
                        if no_test:
                            if len(test_names) == 0:
                                if (buildType == "mvn"):
                                    D_args.append("-DskipTests")
                        if (buildType == "mvn"):
                            if (len(test_names) == 0 and not no_test) or (options.runAllTests == True and not no_test):
                                test_names = [""]

                        if (buildType == "ant"):
                            if (len(test_names) == 0 and not no_test) or (options.runAllTests == True and not no_test):
                                # there are no instrumentations so we read all tests
                                test_names = mutation_db.fetch_all_coverage()

                        if (buildType == "gradle"):
                            if (len(test_names) == 0 and not no_test) or (options.runAllTests == True and not no_test):
                                # No per-line instrumentation found -> run all tests (no filtering)
                                test_names = [""]
                        if buildType == "ant":
                            buildFile_ = os.path.join(
                                build_directory, "build.xml" + str(mutant_id))
                        elif buildType == "mvn":
                            buildFile_ = os.path.join(
                                build_directory, "pom.xml" + str(mutant_id)
                            )
                        elif buildType == "gradle":
                            # Do not override Gradle build files via CLI flags; keep original build scripts.
                            buildFile_ = buildFile
                        # Make sure the per-mutant build file exists before LineCoverage._prepare_* reads it.
                        if buildType in ("ant", "mvn"):
                            shutil.copy2(buildFile, buildFile_)
                        if buildType in ("ant", "mvn"):
                            with resources.as_file(
                                resources.files("mediumdarwin")
                                .joinpath("jar")
                                .joinpath("clover_db_extractor.jar")
                            ) as jar_path:
                                line_coverage = LineCoverage(
                                    project_path=build_directory,
                                    clover_db_extractor_path=jar_path,
                                    build_file_path=buildFile_,
                                    build_type=build_command[0],
                                    sqlDB_path=self.sqlDBPath,
                                    D_args=D_args,
                                    runAllTests=options.runAllTests,
                                    timeout=int(options.initial_timeout),
                                    source_path=options.sourcePath,
                                )
                        if buildType in ("ant", "mvn"):
                            includeFile_ = os.path.join(
                                targetDir, "include" + str(mutant_id)
                            )
                            if buildType == "ant":
                                line_coverage._prepare_build_xml(
                                    include_file=includeFile_,
                                    junit_target=options.junitTargetName,
                                    subsumption=options.isSubsumptionActive,
                                )
                                line_coverage.add_tests_to_build_xml(
                                    junit_target=options.junitTargetName,
                                    report_path=os.path.join(
                                        targetDir, str(
                                            mutant_id) + "-test_reports"
                                    ),
                                    covered_tests=test_names,
                                    subsumption=options.isSubsumptionActive,
                                )
                            elif buildType == "mvn":
                                line_coverage._prepare_pom(
                                    include_file_add=includeFile_)
                                line_coverage.add_tests_to_pom_xml(
                                    include_tests_file=includeFile_,
                                    report_path=os.path.join(
                                        targetDir, str(
                                            mutant_id) + "-test_reports"
                                    ),
                                    covered_tests=test_names,
                                    subsumption=options.isSubsumptionActive,
                                )
                    test_command_ = test_command.copy()
                    if (no_test):
                        if (buildType == "mvn"):
                            test_command_.extend(D_args)
                    test_command_ = change_build_file(
                        test_command_.copy(), buildFile_
                    )
                    if options.isCoverageActive and buildType == "gradle" and (options.runAllTests == False) and (not no_test):
                        # Only filter when we have a non-empty selected set.
                        if isinstance(test_names, list) and test_names != [""]:
                            selected_file = write_selected_tests_file(
                                os.path.join(
                                    targetDir,
                                    "include" + str(mutant_id) +
                                    ".selected-tests.txt",
                                ),
                                test_names,
                            )
                            test_command_ = add_gradle_test_selection_via_file(
                                test_command_, build_directory, selected_file
                            )
                    # CRITICAL: For Gradle, always add isolation flags (both coverage and schemata-only paths)
                    # This ensures parallel-safe report handling and correct report directory redirection
                    if buildType == "gradle":
                        # Clear reports directory before test to ensure we get fresh results for this mutant
                        report_path_for_mutant = os.path.join(
                            targetDir, str(mutant_id) + "-test_reports")
                        shutil.rmtree(report_path_for_mutant,
                                      ignore_errors=True)
                        os.makedirs(report_path_for_mutant, exist_ok=True)
                        test_command_ = add_gradle_isolation(
                            test_command_,
                            project_path=build_directory,
                            run_id=str(mutant_id),
                            reports_dir=report_path_for_mutant,
                        )
                    s_time = time.time()
                    (
                        process_test_killed,
                        process_test_exit_code,
                        run_output_test,
                        time_delta
                    ) = timeoutAlternative(
                        test_command_.copy(),
                        workingDirectory=build_directory,
                        timeout=int(options.timeout),
                        failMessage=options.fail_string,
                        activeMutants=subset,
                    )
                    self.test_time += s_time - time.time()
                    targetTextOutputFile = str(
                        os.path.join(
                            targetDir, str(mutant_id) + ".txt"
                        )
                    )
                    if buildType == "ant":
                        backupFile = os.path.join(
                            targetDir,
                            str(mutant_id) + ".build.xml",
                        )
                    elif buildType == "mvn":
                        backupFile = os.path.join(
                            targetDir,
                            str(mutant_id) + ".pom.xml",
                        )
                    if backupFile == None or buildFile_ == None:
                        print("build file not found no backup is taken")
                    else:
                        if options.isCoverageActive:
                            if debug:
                                print("moving: " + buildFile_ +
                                      " -> " + backupFile)
                            shutil.move(buildFile_, backupFile)
                        else:
                            if debug:
                                print("copying: " + buildFile_ +
                                      " -> " + backupFile)
                            shutil.copy(buildFile_, backupFile)
                    if options.isCoverageActive and buildType in ("mvn", "ant"):
                        os.remove(line_coverage.build_file_path + ".bak")
                        del line_coverage
                    with open(targetTextOutputFile, "w") as contentFile:
                        contentFile.write(" ".join(test_command_) + "\n\r")
                        contentFile.write(str(run_output_test))

                    # Copy surefire/JUnit XML reports to per-mutant folder (needed for database insertion)
                    report_path_for_mutant = os.path.join(
                        targetDir, str(mutant_id) + "-test_reports"
                    )
                    try:
                        if buildType == "mvn":
                            default_reports_dir = os.path.join(
                                build_directory, "target", "surefire-reports")
                            if os.path.isdir(default_reports_dir):
                                for xml_file in Path(default_reports_dir).glob("*.xml"):
                                    if xml_file.is_file():
                                        shutil.copy2(str(xml_file), os.path.join(
                                            report_path_for_mutant, xml_file.name))
                        elif buildType == "ant":
                            possible_dirs = [
                                os.path.join(build_directory, "test-results"),
                                os.path.join(build_directory,
                                             "target", "test-results"),
                                build_directory,
                            ]
                            for possible_dir in possible_dirs:
                                if os.path.isdir(possible_dir):
                                    xml_files = list(
                                        Path(possible_dir).glob("*.xml"))
                                    if xml_files:
                                        for xml_file in xml_files:
                                            if xml_file.is_file():
                                                shutil.copy2(str(xml_file), os.path.join(
                                                    report_path_for_mutant, xml_file.name))
                                        break
                        elif buildType == "gradle":
                            # For Gradle, reports are written directly to report_path_for_mutant via md.reportsDir
                            # (similar to how Maven writes to a per-mutant directory via pom.xml configuration)
                            # No copying needed - reports should already be in the correct location
                            pass
                    except Exception:
                        # best-effort; missing reports shouldn't crash the run
                        pass

                    if process_test_killed or process_test_exit_code:
                        if debug:
                            print("killed: " + str(subset))
                        mutant_id_str = str(mutant_id)
                        if process_test_killed:
                            res = (mutant_id, subset,
                                   Database.RES_ID_TIMEOUT, file)
                            if mutant_id_str not in res_dict[res[3]]["timeoutList"]:
                                res_dict[res[3]]["timeoutList"].append(
                                    mutant_id_str)
                            if mutant_id_str not in res_dict[res[3]]["killedList"]:
                                res_dict[res[3]]["killedList"].append(
                                    mutant_id_str)
                            msg = "timeout"
                            result_code = Database.RES_ID_TIMEOUT
                            # For timeout, insert summary record
                            mutation_db.insert_data(
                                "mutant_test",
                                "mutant_id, test_id, result, time, message",
                                [
                                    res[0],
                                    Database.NO_INFO,
                                    result_code,
                                    str(time_delta),
                                    msg,
                                ],
                            )
                        else:
                            res = (mutant_id, subset,
                                   Database.RES_ID_KILLED_MUTANT, file)
                            if mutant_id_str not in res_dict[res[3]]["testFailureList"]:
                                res_dict[res[3]]["testFailureList"].append(
                                    mutant_id_str)
                            if mutant_id_str not in res_dict[res[3]]["killedList"]:
                                res_dict[res[3]]["killedList"].append(
                                    mutant_id_str)
                            msg = "killed"
                            result_code = Database.RES_ID_KILLED_MUTANT
                            # Always parse surefire reports to get individual test results
                            self.updateMutationTestTable(
                                options=options, mutationDatabase=mutation_db, file_name=file, mutant_id=mutant_id)
                    else:
                        if debug:
                            print("Survived: " + str(subset))
                        res = (mutant_id, subset,
                               Database.RES_ID_SURVIVED_MUTANT, file)
                        mutant_id_str = str(mutant_id)
                        if mutant_id_str not in res_dict[res[3]]["survivedList"]:
                            res_dict[res[3]]["survivedList"].append(
                                mutant_id_str)
                        msg = "survived"
                        # Always parse surefire reports to get individual test results
                        self.updateMutationTestTable(
                            options=options, mutationDatabase=mutation_db, file_name=file, mutant_id=mutant_id)
                    # reverse the mutations after running the compile time mutant
                    for c_a in compile_again:
                        # compile_mutations_[mutation][1].reverse_mutation()
                        for i in range(len(compile_mutations_[c_a])):
                            compile_mutations_[c_a][i][0].apply_reverse_mutation_in_place(
                                compile_mutations_[c_a][i][1],
                                compile_mutations_[c_a][i][2],
                                compile_mutations_[c_a][i][3],)

                    schemataFile = os.path.join(
                        self.LittleDarwinResultsPath,
                        os.path.relpath(file, options.sourcePath),
                        "mutant_schemata.java"
                    )
                    if os.path.isfile(schemataFile):
                        shutil.copyfile(
                            schemataFile, file)
                else:
                    # Initialize variables for schemata-only path
                    test_names = []
                    no_test = False
                    buildFile_ = buildFile
                    test_command_ = test_command.copy()
                    # For schemata-only path, ensure test_command_ is properly initialized
                    # and will be modified with Gradle isolation flags below
                    if options.isCoverageActive:
                        buildFile_ = None
                        D_args = []
                        if buildType == "mvn":
                            D_args = return_D_arguments(" ".join(test_command))
                            buildFile_ = os.path.join(
                                build_directory, "pom.xml" + str(mutant_id)
                            )
                        elif buildType == "ant":
                            buildFile_ = os.path.join(
                                build_directory, "build.xml" + str(mutant_id)
                            )
                        elif buildType == "gradle":
                            # Gradle build scripts should not be copied per-mutant here.
                            # Gradle test filtering/isolation is done via command flags/init scripts.
                            buildFile_ = buildFile
                        # Only create per-mutant build files for tools that are actually rewritten.
                        if buildType in ("mvn", "ant") and buildFile_ is not None:
                            shutil.copy2(buildFile, buildFile_)
                        lines = mutation_db.fetch_file_mutant_by_mutation_ID(
                            mutant_id, options=options)
                        test_names = list()
                        for line in lines:
                            test_names.extend(
                                mutation_db.fetch_coverage(file, line[2], options=options))
                        os.makedirs(
                            os.path.join(targetDir, str(
                                mutant_id) + "-test_reports"),
                            exist_ok=True,
                        )
                        non_covered = False
                        while ("-",) in test_names:
                            non_covered = True
                            test_names.remove(("-",))
                        if non_covered:
                            if len(test_names) == 0:
                                res = (mutant_id, subset,
                                       Database.RES_ID_NON_COVERED, file)
                                msg = "non-covered"
                                res_dict[res[3]]["nonCoveredList"].append(
                                    str(res[0]))
                                mutation_db.insert_data(
                                    "mutant_test",
                                    "mutant_id, test_id, result, time, message",
                                    [
                                        res[0],
                                        Database.INSTURMENTED_NOT_COVERED,
                                        Database.RES_ID_NON_COVERED,
                                        "0",
                                        msg,
                                    ],
                                )
                                if buildType in ("mvn", "ant") and buildFile_ and buildFile_ != buildFile and os.path.isfile(buildFile_):
                                    os.remove(buildFile_)
                                continue
                        no_test = False
                        while ("?",) in test_names:
                            no_test = True
                            test_names.remove(("?",))
                        if no_test:
                            if len(test_names) == 0:
                                if (buildType == "mvn"):
                                    D_args.append("-DskipTests")
                        if (buildType == "mvn"):
                            if (len(test_names) == 0 and not no_test) or (options.runAllTests == True and not no_test):
                                test_names = [""]

                        if (buildType == "ant"):
                            if (len(test_names) == 0 and not no_test) or (options.runAllTests == True and not no_test):
                                # there are no instrumentations so we read all tests
                                test_names = mutation_db.fetch_all_coverage()
                        if (buildType == "gradle"):
                            if (len(test_names) == 0 and not no_test) or (options.runAllTests == True and not no_test):
                                test_names = [""]
                        with resources.as_file(
                            resources.files("mediumdarwin")
                            .joinpath("jar")
                            .joinpath("clover_db_extractor.jar")
                        ) as jar_path:
                            if buildType in ("mvn", "ant"):
                                line_coverage = LineCoverage(
                                    project_path=build_directory,
                                    clover_db_extractor_path=jar_path,
                                    build_file_path=buildFile_,
                                    build_type=build_command[0],
                                    sqlDB_path=self.sqlDBPath,
                                    D_args=D_args,
                                    runAllTests=options.runAllTests,
                                    timeout=int(options.initial_timeout),
                                    source_path=options.sourcePath,
                                )
                                includeFile_ = os.path.join(
                                    targetDir, "include" + str(mutant_id)
                                )
                                if buildType == "mvn":
                                    line_coverage._prepare_pom(
                                        include_file_add=includeFile_)
                                    line_coverage.add_tests_to_pom_xml(
                                        include_tests_file=includeFile_,
                                        report_path=os.path.join(
                                            targetDir, str(
                                                mutant_id) + "-test_reports"
                                        ),
                                        covered_tests=test_names,
                                        subsumption=options.isSubsumptionActive,
                                    )
                                elif buildType == "ant":
                                    line_coverage._prepare_build_xml(
                                        include_file=includeFile_,
                                        junit_target=options.junitTargetName,
                                        subsumption=options.isSubsumptionActive,
                                    )
                                    line_coverage.add_tests_to_build_xml(
                                        junit_target=options.junitTargetName,
                                        report_path=os.path.join(
                                            targetDir, str(
                                                mutant_id) + "-test_reports"
                                        ),
                                        covered_tests=test_names,
                                        subsumption=options.isSubsumptionActive,
                                    )
                        test_command_ = test_command.copy()
                        if (no_test):
                            if (buildType == "mvn"):
                                test_command_.extend(
                                    D_args)
                        # For Gradle, do not attempt to override build file
                        test_command_ = change_build_file(
                            test_command_.copy(), buildFile_
                        )
                        # For Gradle, prefer file-based test selection so we also persist the chosen
                        # tests to `include<id>.selected-tests.txt` for debugging/reproducibility.
                        if buildType == "gradle" and (options.runAllTests == False) and (not no_test):
                            if isinstance(test_names, list) and test_names != [""]:
                                selected_file = write_selected_tests_file(
                                    os.path.join(
                                        targetDir,
                                        "include" +
                                        str(mutant_id) + ".selected-tests.txt",
                                    ),
                                    test_names,
                                )
                                test_command_ = add_gradle_test_selection_via_file(
                                    test_command_, build_directory, selected_file
                                )
                        if buildType in ("mvn", "ant"):
                            os.remove(line_coverage.build_file_path + ".bak")
                            del line_coverage
                    # CRITICAL: For Gradle, always add isolation flags (both coverage and schemata-only paths)
                    # This must be OUTSIDE the if options.isCoverageActive block to run for schemata-only runs
                    if buildType == "gradle":
                        # Clear reports directory before test to ensure we get fresh results for this mutant
                        report_path_for_mutant = os.path.join(
                            targetDir, str(mutant_id) + "-test_reports")
                        shutil.rmtree(report_path_for_mutant,
                                      ignore_errors=True)
                        os.makedirs(report_path_for_mutant, exist_ok=True)
                        test_command_ = add_gradle_isolation(
                            test_command_,
                            project_path=build_directory,
                            run_id=str(mutant_id),
                            reports_dir=report_path_for_mutant,
                        )
                    targetTextOutputFile = str(
                        os.path.join(
                            targetDir, str(mutant_id) + ".txt"
                        )
                    )
                    # Reports directory is already created above for Gradle, create for others
                    if buildType != "gradle":
                        os.makedirs(
                            os.path.join(targetDir, str(
                                mutant_id) + "-test_reports"),
                            exist_ok=True,
                        )
                    function_calls.append(
                        (mutant_id, subset, targetTextOutputFile, test_command_, file)
                    )
        # clean the project once before running tests because of the previous builds (test command is indepndent of the build command)
        if options.cleanUp != "***dummy***":
            s_time = time.time()
            (
                process_clean_killed,
                process_clean_exit_code,
                run_output_clean,
                time_delta
            ) = timeoutAlternative(
                clean_command,
                workingDirectory=build_directory,
                timeout=int(options.timeout),
                failMessage=options.fail_string,
            )
            self.clean_time += time.time() - s_time
        (
            process_build_killed,
            process_build_exit_code,
            run_output_build,
            time_delta
        ) = timeoutAlternative(
            options.buildCommand.split(
                ",") if options.initialBuildCommand == "***dummy***" else getCommand(options.initialBuildCommand),
            workingDirectory=build_directory,
            timeout=int(options.initial_timeout),
            failMessage=options.fail_string,
        )
        # create a parallel execution list of the test commands
        parallel = Parallel(n_jobs=JOBS_NO, return_as="generator_unordered")
        output_generator = parallel(
            delayed(self.run_test)(
                mutation=mutation,
                test_command=test_command,
                source_directory=build_directory,
                mutant_id=mutant_id,
                targetTextOutputFile=targetTextOutputFile,
                coverage=options.isCoverageActive,
                timeout=int(options.timeout),
                fail_message=options.fail_string,
                file=file
            )
            for (
                mutant_id,
                mutation,
                targetTextOutputFile,
                test_command,
                file
            ) in function_calls
        )
        stdscr = initscr()
        s_time = time.time()
        with open(
            os.path.join(mutantsPath, "output.txt"),
            "w",
        ) as f:
            for item in output_generator:
                msg = ""
                mutant_id_str = str(item[0])
                file = item[3]
                if item[2] == Database.RES_ID_SURVIVED_MUTANT:
                    if mutant_id_str not in res_dict[file]["survivedList"]:
                        res_dict[file]["survivedList"].append(mutant_id_str)
                    msg = "survived"
                elif item[2] == Database.RES_ID_KILLED_MUTANT:
                    if mutant_id_str not in res_dict[file]["testFailureList"]:
                        res_dict[file]["testFailureList"].append(mutant_id_str)
                    if mutant_id_str not in res_dict[file]["killedList"]:
                        res_dict[file]["killedList"].append(mutant_id_str)
                    msg = "killed"
                elif item[2] == Database.RES_ID_BUILD_FAILURE:
                    msg = "build failure"
                    if mutant_id_str not in res_dict[file]["killedList"]:
                        res_dict[file]["killedList"].append(mutant_id_str)
                    if mutant_id_str not in res_dict[file]["buildFailureList"]:
                        res_dict[file]["buildFailureList"].append(
                            mutant_id_str)
                elif item[2] == Database.RES_ID_TIMEOUT:
                    msg = "timeout"
                    if mutant_id_str not in res_dict[file]["killedList"]:
                        res_dict[file]["killedList"].append(mutant_id_str)
                    if mutant_id_str not in res_dict[file]["timeoutList"]:
                        res_dict[file]["timeoutList"].append(mutant_id_str)
                elif item[2] == Database.RES_ID_NON_COVERED:
                    msg = "non-covered"
                    if mutant_id_str not in res_dict[file]["nonCoveredList"]:
                        res_dict[file]["nonCoveredList"].append(mutant_id_str)

                # Always try to parse surefire reports and insert individual test results
                # For special cases (timeout, build failure, non-covered), insert a summary record
                # For normal cases (survived/killed), parse surefire XMLs for detailed test results
                if (item[2] == Database.RES_ID_TIMEOUT) or (item[2] == Database.RES_ID_BUILD_FAILURE) or (item[2] == Database.RES_ID_NON_COVERED):
                    # For these special cases, insert summary record
                    mutation_db.insert_data(
                        "mutant_test",
                        "mutant_id, test_id, result, time, message",
                        [
                            item[0],
                            Database.NO_INFO,
                            item[2],
                            str(item[4]),
                            msg,
                        ],
                    )
                else:
                    # For survived/killed mutants, always parse surefire reports to get individual test results
                    # This populates mutant_test with per-test results regardless of coverage/subsumption flags
                    self.updateMutationTestTable(
                        options=options, mutationDatabase=mutation_db, file_name=item[3], mutant_id=item[0])
                self.print_results(res_dict, start_time)
                refresh()
                f.write(str(item[0]) + " : " + msg + "\n\r")
            self.test_time += time.time() - s_time
            f.write("clean time : " +
                    str(datetime.timedelta(seconds=int(self.clean_time))) + "\n\r")
            f.write("test time : " +
                    str(datetime.timedelta(seconds=int(self.test_time))) + "\n\r")
        # release the terminal
        endwin()
        print("done")
        # output_generator.extend(resList)
        # read the results from the db and generate the HTML report files
        targetHTMLReportFile = os.path.abspath(
            os.path.join(self.LittleDarwinResultsPath, "index.html"))
        from mediumdarwin.ReportGenerator import ReportGenerator
        reportGenerator = ReportGenerator(self.littleDarwinVersion)
        reportGenerator.initiateDatabase(self.LittleDarwinResultsPath)
        htmlReportData = list()
        print("--> Writing the reports: ")
        for file in res_dict.keys():
            print("----> " + file)
            # file is the database file name (normalized relative path like "src/main/java/.../Class.java")
            # Create subdirectory for this class in LittleDarwinResults (keeping .java extension)
            targetDir = os.path.join(self.LittleDarwinResultsPath, file)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir, exist_ok=True)
            targetHTMLOutputFile = os.path.join(
                targetDir, "index.html"
            )
            with open(targetHTMLOutputFile, "w") as contentFile:
                contentFile.write(
                    reportGenerator.generateHTMLReportPerFile(
                        file,  # Use database file name
                        targetHTMLOutputFile,
                        res_dict[file]["survivedList"],
                        res_dict[file]["killedList"],
                        res_dict[file]["nonCoveredList"],
                        res_dict[file]["buildFailureList"],
                        res_dict[file]["testFailureList"],
                        res_dict[file]["timeoutList"],
                        schemata=os.path.relpath(path=os.path.join(
                            targetDir, "mutant_schemata.java"), start=targetDir) if os.path.exists(os.path.join(targetDir, "mutant_schemata.java")) else None
                    )
                )
            # append the information for this file to the reports.
            # 0: file name, 1: survived count, 2: non-covered survived count, 3: killed by build command count, 4: killed by test command, 5: html file name
            htmlReportData.append(
                [
                    file,  # Use database file name
                    len(res_dict[file]["survivedList"]),
                    len(res_dict[file]["nonCoveredList"]),
                    len(res_dict[file]["buildFailureList"]),
                    len(res_dict[file]["testFailureList"]) +
                    len(res_dict[file]["timeoutList"]),
                    targetHTMLOutputFile,
                ]
            )

        # -----------------------------------------------------
        for file in java_io.fileList:
            targetDir = os.path.join(
                self.LittleDarwinResultsPath,
                os.path.relpath(file, options.sourcePath),
            )
            if os.path.isfile(os.path.join(targetDir, "original.java")):
                shutil.copyfile(os.path.join(targetDir, "original.java"), file)
        with open(targetHTMLReportFile, "w") as htmlReportFile:
            htmlReportFile.writelines(
                reportGenerator.generateHTMLFinalReport(
                    htmlReportData, targetHTMLReportFile
                )
            )
        # -----------------------------------------------------
        # write final HTML report.
        return list(output_generator)

    def cleanup_mediumDarwin(self):
        """
        Terminate MediumDarwin
        """
        print("Cleanup MediumDarwin...")
        java_io = JavaIO(self.options.isVerboseActive)
        java_io.listFiles(
            targetPath=os.path.abspath(self.options.sourcePath),
            buildPath=os.path.abspath(self.options.buildPath),
            filterType=self.filterType,
            filterList=self.filterList,
        )
        for file in java_io.fileList:
            originalFile = os.path.join(
                self.LittleDarwinResultsPath,
                os.path.relpath(file, self.options.sourcePath),
                "original.java"
            )
            if os.path.isfile(originalFile):
                shutil.copyfile(
                    originalFile, file)
                print("Restored " + file)

    def __init__(self, mockArgs: list = None):
        print(r"""
        __       __                  __  __                          _______                                     __
       |  \     /  \                |  \|  \                        |       \                                   |  \
       | $$\   /  $$  ______    ____| $$ \$$ __    __  ______ ____  | $$$$$$$\  ______    ______   __   __   __  \$$ _______
       | $$$\ /  $$$ /      \  /      $$|  \|  \  |  \|      \    \ | $$  | $$ |      \  /      \ |  \ |  \ |  \|  \|       \
       | $$$$\  $$$$|  $$$$$$\|  $$$$$$$| $$| $$  | $$| $$$$$$\$$$$\| $$  | $$  \$$$$$$\|  $$$$$$\| $$ | $$ | $$| $$| $$$$$$$\
       | $$\$$ $$ $$| $$    $$| $$  | $$| $$| $$  | $$| $$ | $$ | $$| $$  | $$ /      $$| $$   \$$| $$ | $$ | $$| $$| $$  | $$
       | $$ \$$$| $$| $$$$$$$$| $$__| $$| $$| $$__/ $$| $$ | $$ | $$| $$__/ $$|  $$$$$$$| $$      | $$_/ $$_/ $$| $$| $$  | $$
       | $$  \$ | $$ \$$     \ \$$    $$| $$ \$$    $$| $$ | $$ | $$| $$    $$ \$$    $$| $$       \$$   $$   $$| $$| $$  | $$
        \$$      \$$  \$$$$$$$  \$$$$$$$ \$$  \$$$$$$  \$$  \$$  \$$ \$$$$$$$   \$$$$$$$ \$$        \$$$$$\$$$$  \$$ \$$   \$$

       Copyright (c) 2014 2022 Ali Parsai
       Copyright (c) 2025      MediumDarwin Contributors

       This project builds upon the original work of Ali Parsai and the LittleDarwin mutation testing framework.
       We gratefully acknowledge his foundational contributions, which made this extended version possible.

       This program is free software: you can redistribute it and/or modify it under the terms of the GNU
       General Public License as published by the Free Software Foundation, version 3  of the License, or
       (at your option) any later version.

       This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
       warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the  GNU General Public License for more details.

       You should have received a copy of the GNU General Public License along with this program.
       If not, see <https://www.gnu.org/licenses/>.

       Original author:
       Ali Parsai — https://www.parsai.net/
        """)
        optionParser = OptionParser()
        self.options, self.filterType, self.filterList, higherOrder = parseCmdArgs(
            optionParser, mockArgs
        )
        self.LittleDarwinResultsPath = os.path.join(
            self.options.buildPath, "LittleDarwinResults"
        )
        self.sqlDBPath = os.path.join(
            self.LittleDarwinResultsPath, "mutationdatabase.db"
        )
        self._formatter_warning_emitted = False
        if not os.path.exists(self.LittleDarwinResultsPath):
            os.makedirs(self.LittleDarwinResultsPath, exist_ok=True)

    def main(self):
        """
        Main LittleDarwin Function
        """

        MUTATION_ORDER = self.options.higherOrder
        mutationDatabase2 = Database(self.sqlDBPath)

        # Read HOM definitions from file if --mutation-ids-file is specified
        hom_definitions = []
        if self.options.mutationIdsFile != "***dummy***":
            try:
                with open(self.options.mutationIdsFile, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        try:
                            mutation_id_list = [
                                int(x.strip()) for x in line.split(",") if x.strip()]
                            if mutation_id_list:
                                hom_definitions.append(mutation_id_list)
                        except ValueError:
                            print(
                                f"Warning: Invalid format in {self.options.mutationIdsFile} line {line_num}: {line}")
                            print(
                                "Expected format: comma-separated integers (e.g., '1, 2, 3, 4')")
                            continue
            except FileNotFoundError:
                print(
                    f"Error: Mutation IDs file not found: {self.options.mutationIdsFile}")
                sys.exit(1)
            except Exception as e:
                print(
                    f"Error reading mutation IDs file {self.options.mutationIdsFile}: {e}")
                sys.exit(1)

            if not hom_definitions:
                print(
                    f"Error: No valid HOM definitions found in {self.options.mutationIdsFile}")
                sys.exit(1)

            print(
                f"Loaded {len(hom_definitions)} HOM definitions from {self.options.mutationIdsFile}")
            # Store HOM count for progress tracking
            self.hom_definitions_count = len(hom_definitions)
        else:
            self.hom_definitions_count = None
        if self.options.isBuildActive or self.options.isMutationActive:
            mutationDatabase2.create_tables()
            java_io = JavaIO(self.options.isVerboseActive)
            java_io.listFiles(targetPath=os.path.abspath(self.options.sourcePath), buildPath=os.path.abspath(
                self.options.buildPath), filterType=self.filterType, filterList=self.filterList)
            for f in java_io.fileList:
                mutationDatabase2.insert_file(f, options=self.options)
            build_command = getCommand(self.options.buildCommand)
            clean_command = getCommand(self.options.cleanUp)
            test_command = getCommand(self.options.testCommand)

            build_directory = os.path.abspath(self.options.buildPath)

            buildType = ""
            buildType = detect_build_tool(build_command[0])
            buildFile = return_build_file(" ".join(build_command))
            if buildFile == None:
                if buildType == "ant":
                    buildFile = os.path.join(build_directory, "build.xml")
                elif buildType == "mvn":
                    buildFile = os.path.join(build_directory, "pom.xml")
                elif buildType == "gradle":
                    groovy = os.path.join(build_directory, "build.gradle")
                    kotlin = os.path.join(build_directory, "build.gradle.kts")
                    buildFile = groovy if os.path.isfile(groovy) else (
                        kotlin if os.path.isfile(kotlin) else groovy)
            # initial build check to avoid false results. the system must be able to build cleanly without errors.
            # use build command for the initial build unless it is explicitly provided.
            print("Initial build...", end=" ", flush=True)
            s_time = time.time()
            try:
                processInitialKilled, processInitialExitCode, initialOutput, time_delta = (
                    timeoutAlternative(
                        self.options.buildCommand.split(
                            ",") if self.options.initialBuildCommand == "***dummy***" else getCommand(self.options.initialBuildCommand),
                        workingDirectory=os.path.abspath(
                            self.options.buildPath),
                        timeout=int(self.options.initial_timeout),
                        failMessage=self.options.fail_string,
                    )
                )
                # workaround for older python versions
                if processInitialKilled or processInitialExitCode:
                    raise subprocess.CalledProcessError(
                        1 if processInitialKilled else processInitialExitCode,
                        self.options.buildCommand.split(
                            ",") if self.options.initialBuildCommand == "***dummy***" else getCommand(self.options.initialBuildCommand),
                        initialOutput,
                    )
                with open(
                    os.path.abspath(os.path.join(
                        self.LittleDarwinResultsPath, "initialbuild.txt")), "w"
                ) as contentFile:
                    contentFile.write(str(initialOutput))
                # run line coverage and store the results
                if self.options.isCoverageActive == True:
                    line_coverage = None
                    print("Running clover test coverage collection...",
                          end=" ", flush=True)
                    with resources.as_file(
                        resources.files("mediumdarwin")
                        .joinpath("jar")
                        .joinpath("clover_db_extractor.jar")
                    ) as jar_path:
                        line_coverage = LineCoverage(
                            project_path=build_directory,
                            clover_db_extractor_path=jar_path,
                            build_file_path=buildFile,
                            build_type=build_command[0],
                            sqlDB_path=self.sqlDBPath,
                            D_args=return_D_arguments(" ".join(test_command)),
                            runAllTests=self.options.runAllTests,
                            timeout=int(self.options.initial_timeout),
                            source_path=self.options.sourcePath,
                        )
                        line_coverage.run_clover(
                            junit_target=self.options.junitTargetName,
                            test_target=(
                                "test" if buildType in (
                                    "mvn", "gradle") else self.options.testTargetName
                            ),
                        )
                        if buildType in ("mvn", "ant"):
                            line_coverage.restore_the_build_file()
                print("done.\n\n")
            except subprocess.CalledProcessError as exception:
                initialOutput = exception.output
                with open(
                    os.path.abspath(os.path.join(
                        self.LittleDarwinResultsPath, "initialbuild.txt")), "w"
                ) as contentFile:
                    initialOutput = initialOutput
                    contentFile.write(
                        str(initialOutput).replace("\\r\\n", "\n")
                        + "\n Command: "
                        + " ".join(exception.cmd)
                    )
                print("failed.\n")
                print(
                    "Initial build failed. Try building the system manually first to make sure it can be built. "
                    + "Take a look at "
                    + os.path.abspath(os.path.join(self.LittleDarwinResultsPath,
                                                   "initialbuild.txt"))
                    + " to find out why this happened."
                )
                sys.exit(3)
            self.compile_time += time.time() - s_time

            if self.options.cleanUp != "***dummy***":
                s_time = time.time()
                (
                    process_clean_killed,
                    process_clean_exit_code,
                    run_output_clean,
                    time_delta
                ) = timeoutAlternative(
                    clean_command,
                    workingDirectory=os.path.abspath(self.options.buildPath),
                    timeout=int(self.options.timeout),
                    failMessage=self.options.fail_string,
                )
                self.clean_time += time.time() - s_time

        # *****************************************************************************************************************
        # ---------------------------------------- mutant generation phase ------------------------------------------------
        # *****************************************************************************************************************
        if self.options.isMutationActive:
            (
                build_failures,
                file_mutations_dict,
            ) = self.mutant_schemata_generation(
                self.options,
                self.filterType,
                self.filterList,
                mutationDatabase2,
                False
            )
            mutant_ID = -1
            print("--> Writing mutant data to the DB: ")

            # Backfill coverage for mutations that weren't covered by tests
            # This must be done AFTER mutations are inserted into the database
            # For Gradle: use backfill (javatraceragent)
            # For Ant/Maven: clover extractor already did the job, no backfill needed
            if self.options.isCoverageActive and self.sqlDBPath and buildType == "gradle":
                try:
                    line_coverage = LineCoverage(
                        self.options.buildPath,
                        None,  # clover_db_extractor_path
                        None,  # build_file_path
                        "",  # build_type
                        self.sqlDBPath,
                        source_path=self.options.sourcePath,
                    )
                    line_coverage.backfill_mutation_coverage(
                        options=self.options)
                    print("--> Backfilled coverage for mutations (Gradle)")
                except Exception as e:
                    print(
                        f"Warning: Failed to backfill mutation coverage: {e}")

            # Check if mutation IDs file is requested (takes precedence over normal generation)
            if self.options.mutationIdsFile != "***dummy***" and hom_definitions:
                # Use HOM definitions from file
                # Iterate over HOM definitions first, then collect mutations across all files
                print("--> Processing HOM definitions from file")
                hom_start_id = mutant_ID + 1
                # Collect warnings: missing IDs and skipped HOMs
                missing_ids_set = set()
                skipped_homs_no_mutations = []  # HOMs with no mutations found in any file
                # HOMs skipped because mutations span multiple files
                skipped_homs_multiple_files = []
                generated_homs_count = 0  # Track number of HOMs actually generated
                for hom_idx, mutation_id_list in enumerate(hom_definitions):
                    # Collect mutations with specified IDs, grouped by file
                    mutations_by_file = {}

                    for file in file_mutations_dict.keys():
                        file_mutations = [
                            mut_id for mut_id in file_mutations_dict[file].keys()
                            if mut_id in mutation_id_list
                        ]
                        if file_mutations:
                            mutations_by_file[file] = file_mutations

                    # Skip this HOM if no mutations match
                    if not mutations_by_file:
                        skipped_homs_no_mutations.append(hom_idx + 1)
                        continue

                    # Ensure all mutations belong to the same file
                    if len(mutations_by_file) > 1:
                        # Mutations span multiple files - skip this HOM
                        skipped_homs_multiple_files.append(hom_idx + 1)
                        continue

                    # All mutations are from a single file
                    primary_file = list(mutations_by_file.keys())[0]
                    selected_mutations = mutations_by_file[primary_file]

                    # Check if all requested mutation IDs were found
                    found_ids = set(selected_mutations)
                    missing_ids = set(mutation_id_list) - found_ids
                    if missing_ids:
                        # Store warning instead of printing immediately
                        missing_ids_set.update(missing_ids)

                    # Create a single mutant with all selected mutations for this HOM (all from the same file)
                    mutant_ID += 1
                    generated_homs_count += 1
                    my_set = set()
                    build_failure_occurred = False
                    for mutation in selected_mutations:
                        my_set.add(mutation)
                        mutationDatabase2.insert_mutant(
                            mutant_ID, mutation)
                        if mutation in build_failures:
                            res = (mutant_ID, tuple(selected_mutations),
                                   Database.RES_ID_BUILD_FAILURE, primary_file)
                            msg = "build failure"
                            mutationDatabase2.insert_data(
                                "mutant_test",
                                "mutant_id, test_id, result, time, message",
                                [
                                    res[0],
                                    Database.NO_TEST,
                                    Database.RES_ID_BUILD_FAILURE,
                                    "0",
                                    msg,
                                ],
                            )
                            build_failure_occurred = True
                            break

                    if (hom_idx + 1) % 100 == 0:
                        print(
                            f"  Processed {hom_idx + 1}/{len(hom_definitions)} HOM definitions...")

                # Print aggregated warnings
                if missing_ids_set:
                    print(
                        f"Warning: Some mutation IDs were not found: {missing_ids_set}")
                if skipped_homs_no_mutations:
                    print(
                        f"Warning: {len(skipped_homs_no_mutations)} HOM(s) were skipped because no mutations were found in any file: {skipped_homs_no_mutations[:20]}{'...' if len(skipped_homs_no_mutations) > 20 else ''}")
                if skipped_homs_multiple_files:
                    print(
                        f"Warning: {len(skipped_homs_multiple_files)} HOM(s) were skipped because mutations span multiple files: {skipped_homs_multiple_files[:20]}{'...' if len(skipped_homs_multiple_files) > 20 else ''}")

                mutants_created = mutant_ID + 1 - hom_start_id
                total_loaded = len(hom_definitions)
                total_generated = generated_homs_count
                total_skipped = total_loaded - total_generated

                print(
                    f"\n--> Created {mutants_created} mutants from {len(hom_definitions)} HOM definitions")

                # Print comprehensive HOM generation summary
                print(f"\n=== HOM Generation Summary ===")
                print(f"Loaded HOM definitions: {total_loaded}")
                print(f"Generated HOMs: {total_generated}")
                print(f"Skipped HOMs: {total_skipped}")
                if skipped_homs_no_mutations:
                    print(
                        f"  - Skipped due to no mutations found in any file: {len(skipped_homs_no_mutations)}")
                    if len(skipped_homs_no_mutations) <= 50:
                        print(f"    HOM IDs: {skipped_homs_no_mutations}")
                    else:
                        print(
                            f"    HOM IDs (first 50): {skipped_homs_no_mutations[:50]}...")
                if skipped_homs_multiple_files:
                    print(
                        f"  - Skipped due to mutations spanning multiple files: {len(skipped_homs_multiple_files)}")
                    if len(skipped_homs_multiple_files) <= 50:
                        print(f"    HOM IDs: {skipped_homs_multiple_files}")
                    else:
                        print(
                            f"    HOM IDs (first 50): {skipped_homs_multiple_files[:50]}...")
            else:
                # Normal mutant generation using combinations
                for file in file_mutations_dict.keys():
                    print("----> " + file)
                    for L in range(1, (MUTATION_ORDER + 1)):
                        for subset in itertools.combinations(file_mutations_dict[file].keys(), L):
                            mutant_ID += 1
                            my_set = set()
                            for mutation in subset:
                                my_set.add(mutation)
                                mutationDatabase2.insert_mutant(
                                    mutant_ID, mutation)
                                if mutation in build_failures:
                                    res = (mutant_ID, subset,
                                           Database.RES_ID_BUILD_FAILURE, file)
                                    msg = "build failure"
                                    mutationDatabase2.insert_data(
                                        "mutant_test",
                                        "mutant_id, test_id, result, time, message",
                                        [
                                            res[0],
                                            Database.NO_TEST,
                                            Database.RES_ID_BUILD_FAILURE,
                                            "0",
                                            msg,
                                        ],
                                    )
                                    break
            print("-------------------------------------")
        if self.options.isBuildActive:
            results = mutationDatabase2.fetch_mutations()
            java_parse = JavaParse(False)
            Mutation.reverse_mutation_dict = dict()
            Mutation.mutation_dict = dict()
            for res in results:
                Mutation.mutation_dict[int(res[0])] = (
                    eval(res[9]), eval(res[8]), eval(res[10]))
                for i in range(len(Mutation.mutation_dict[int(res[0])][0])):
                    Mutation.mutation_dict[int(res[0])][1][i] = java_parse.Json2Tree(
                        Mutation.mutation_dict[int(res[0])][1][i])

                    Mutation.mutation_dict[int(res[0])][0][i] = int(
                        Mutation.mutation_dict[int(res[0])][0][i])
                    Mutation.mutation_dict[int(
                        res[0])][2][i] = Mutation.mutation_dict[int(res[0])][2][i]

            mutants_dict_ = mutationDatabase2.construct_mutant_dict(
                self.options)
            compile_mutations_files = mutationDatabase2.construct_compile_mutations(
                self.options)
            output_generator = self.run_mutant_schemata(
                mutants_dict_,
                # de_pickled_build_failures,
                compile_mutations_files,
                mutationDatabase2,
                self.options,
            )
            count = 0
            for item in output_generator:
                count += item[2]
            print(str(count) + "/" + str(len(output_generator)))

        if self.options.isSubsumptionActive:
            self.subsumptionAnalysisPhase(self.options)
        mutationDatabase2.close_connection()
