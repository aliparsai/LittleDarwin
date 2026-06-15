"""Shared helper functions used across MediumDarwin modules.

This module centralizes process execution helpers, command parsing, subclass
introspection, and junit XML parsing utilities.
"""
import signal
import platform
import sys
import threading
import re
from shutil import which
import os
import shutil
import subprocess
import tempfile
from mediumdarwin.JavaParser import JavaParser
from mediumdarwin.JavaParse import JavaParse
import xml.etree.ElementTree as ET
import time
import shlex


class MutationOperator(object):
    """Base class for mutation operators used for type discovery."""
    """ """
    instantiable = True
    metaTypes = ["Generic"]

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants=False,
        generateMutations=True,
    ):
        self.sourceTree = sourceTree
        self.sourceCode = sourceCode
        self.color = "#FFFFF0"
        self.mutatorType = "GenericMutationOperator"
        self.allNodes = list()  # populated by findNodes
        self.mutableNodes = list()  # populated by filterCriteria
        self.mutations = list()  # populated by generateMutations
        self.mutants = list()  # populated by generateMutants
        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        self.mutations_searched = False
        if self.generateMutants_:
            self.generateMutations_ = True
        self.javaParseObject = javaParseObject

    def findNodes(self):
        """Find nodes that match operator criteria (to be implemented by subclasses)."""
        pass

    def filterCriteria(self):
        """Filter nodes that do not match the operator criteria (to be implemented by subclasses)."""
        pass

    def generateMutations(self):
        """Generate mutation descriptions (to be implemented by subclasses)."""
        pass

    def generateMutants(self):
        """Materialize mutant instances (to be implemented by subclasses)."""
        pass

    @property
    def cssClass(self):
        """Return CSS class fragment representing this operator's background color."""
        return ".{classname} {{ background: {color}; }} ".format(
            classname=self.mutatorType, color=self.color
        )


def return_build_file(command):
    """Extract a build file path (e.g., pom.xml or build.xml) from a command string.

    Args:
        command: Raw command string (space-separated) that may include -f/--file/-buildfile flags.

    Returns:
        The path passed to a build-file flag if present; otherwise None.
    """
    args = shlex.split(command)
    file = None
    i = 0
    while i < len(args):
        # Maven: -f/--file, Ant: -buildfile
        if args[i] in ["-f", "--file", "-buildfile"]:
            return args[i + 1]
        i += 1
    return file


def detect_build_tool(cmd0: str) -> str:
    """Detect build tool kind from the first command token.

    Args:
        cmd0: First token of a command (may be a bare executable name or a full path).

    Returns:
        One of: "mvn", "ant", "gradle", or "" if unknown.
    """
    if not cmd0:
        return ""
    base = os.path.basename(cmd0).lower()
    for ext in (".bat", ".cmd", ".exe"):
        if base.endswith(ext):
            base = base[: -len(ext)]
            break
    if base in {"mvn", "mvnw"}:
        return "mvn"
    if base in {"ant"}:
        return "ant"
    if base in {"gradle", "gradlew"}:
        return "gradle"
    return ""


def add_gradle_test_filters(command_tokens, covered_tests):
    """Append Gradle test filters (--tests) for the given covered tests.

    Args:
        command_tokens: Command list to execute (e.g., ["gradle", "test"]).
        covered_tests: Items from SQLite fetches, typically tuples like ("pkg.Test#method",).

    Returns:
        A new command list with `--tests <pattern>` tokens appended. Patterns are normalized to
        Gradle's expected format ("pkg.Test.method").
    """
    if not covered_tests:
        return command_tokens
    patterns = []
    for t in covered_tests:
        if t == "":
            continue
        if isinstance(t, tuple):
            t = t[0]
        if not t:
            continue
        t = t.replace("$", ".").replace("#", ".")
        patterns.append(t)
    patterns = sorted(set(patterns))
    if not patterns:
        return command_tokens
    out = list(command_tokens)
    for p in patterns:
        out.extend(["--tests", p])
    return out


def normalize_test_name_for_gradle(test_name: str) -> str:
    """Normalize a test identifier to Gradle `--tests`/TestFilter pattern format.

    MediumDarwin stores test names as 'pkg.Class#method' (Ant style) or 'pkg.Class.method'.
    Gradle expects 'pkg.Class.method' (or just 'pkg.Class').
    """
    if not test_name:
        return ""
    return test_name.replace("$", ".").replace("#", ".").strip()


def write_selected_tests_file(target_file: str, covered_tests) -> str:
    """Write selected tests to a file (one pattern per line).

    Args:
        target_file: Path to write.
        covered_tests: iterable of tuples/strings from the DB (e.g., [("a.b.T#t",), ...]).

    Returns:
        The written file path.
    """
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    patterns = []
    for t in covered_tests or []:
        if t == "":
            continue
        if isinstance(t, tuple):
            t = t[0]
        t = normalize_test_name_for_gradle(t)
        if t:
            patterns.append(t)
    # Keep file deterministic and compact
    patterns = sorted(set(patterns))
    with open(target_file, "w", encoding="utf-8") as f:
        for p in patterns:
            f.write(p + "\n")
    return target_file


def ensure_gradle_test_selection_init_script(project_path: str) -> str:
    """Create (if needed) a Gradle init script that loads test filters from a file.

    The selected tests file path is passed via: -Dmd.includeTestsFile=<path>

    This function is parallel-safe: uses atomic file writing to avoid race conditions.
    """
    init_dir = os.path.join(project_path, "LittleDarwinResults")
    os.makedirs(init_dir, exist_ok=True)
    init_path = os.path.join(init_dir, "md-test-selection.init.gradle")
    if os.path.isfile(init_path):
        return init_path

    script = r"""
allprojects {
    tasks.withType(Test).configureEach { t ->
        def f = System.getProperty('md.includeTestsFile')
        if (f != null && !f.isEmpty()) {
            def file = new File(f)
            if (file.exists()) {
                def patterns = file.readLines().collect { line ->
                    // Strip surrounding quotes if present, but preserve the pattern
                    def trimmed = line?.trim()
                    if (trimmed && trimmed.length() >= 2) {
                        if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
                            (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
                            trimmed = trimmed.substring(1, trimmed.length() - 1)
                        }
                    }
                    trimmed
                }.findAll { it && !it.isEmpty() }
                if (!patterns.isEmpty()) {
                    // Apply filter to all Test tasks
                    // CRITICAL: When multiple test frameworks (JUnit, TestNG, Spock) are configured,
                    // each test task must handle filtering independently. If a filter doesn't match
                    // tests in one framework's task, that task can be skipped, preventing other
                    // frameworks' tests from running. We ensure each task runs independently.
                    t.filter {
                        setFailOnNoMatchingTests(false)
                        patterns.each { p ->
                            // Use includeTestsMatching for all patterns
                            // This should work for both patterns with spaces (Spock) and without (JUnit/TestNG)
                            // The pattern is used as-is after stripping quotes
                            // For JUnit/TestNG: patterns like "pkg.Class.method" should match
                            // For Spock: patterns like "pkg.Class.method name" should match
                            includeTestsMatching(p)
                            // For patterns with method names (containing a dot but no spaces),
                            // also try matching the class name alone and with wildcards
                            // This helps when test frameworks identify tests differently
                            if (p.contains('.') && !p.contains(' ')) {
                                def parts = p.split('\\.')
                                if (parts.length > 1) {
                                    // Try class-level pattern (all tests in the class)
                                    def className = parts[0..-2].join('.')
                                    def methodName = parts[-1]
                                    includeTestsMatching(className)
                                    // Also try with wildcard pattern for method name
                                    // JUnit/TestNG might identify tests as "pkg.Class.method" or "pkg.Class#method"
                                    includeTestsMatching(className + ".*")
                                    includeTestsMatching(className + "#*")
                                    // Try exact match using includeTest (for JUnit/TestNG)
                                    try {
                                        includeTest(className, methodName)
                                    } catch (Throwable ignored) {
                                        // includeTest might not be available or might fail, that's OK
                                    }
                                }
                            }
                        }
                    }
                    // CRITICAL: Ensure task runs even if no tests match (important for multi-framework setups)
                    // This prevents tasks from being skipped when they have no matching tests.
                    // Without this, if one framework's task has no matches, it can be skipped,
                    // preventing other frameworks' tests from running.
                    t.onlyIf { true }
                    // Also ensure the task doesn't get marked as UP-TO-DATE when no tests match
                    t.outputs.upToDateWhen { false }
                }
            }
        }
    }
}
"""
    # Atomic file write: write to temp file, then rename (rename is atomic on most filesystems)
    # This prevents race conditions when multiple processes create the file in parallel
    try:
        # Use NamedTemporaryFile with delete=False, then rename
        fd, temp_path = tempfile.mkstemp(
            dir=init_dir, suffix='.gradle', prefix='.tmp-')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(script.strip() + "\n")
            # Atomic rename - if target exists, another process created it (which is fine)
            try:
                os.replace(temp_path, init_path)
            except (OSError, FileExistsError):
                # Another process created it first, remove our temp file
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
                # Double-check the file exists now
                if not os.path.isfile(init_path):
                    raise
        except Exception:
            # Clean up temp file on error
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise
    except Exception:
        # If atomic write failed, check if file was created by another process
        if os.path.isfile(init_path):
            return init_path
        raise
    return init_path


def ensure_gradle_isolation_init_script(project_path: str) -> str:
    """Create (if needed) a Gradle init script to isolate outputs per run.

    Controlled by system properties:
      -Dmd.runId=<string>        (required to enable isolation)
      -Dmd.reportsDir=<path>     (optional; where to write JUnit XML reports)

    Effects:
      - Sets each project's buildDir under LittleDarwinResults/gradle-build/<runId>/...
      - Redirects JUnit XML outputs to md.reportsDir when provided

    This function is parallel-safe: uses atomic file writing to avoid race conditions.
    """
    init_dir = os.path.join(project_path, "LittleDarwinResults")
    os.makedirs(init_dir, exist_ok=True)
    init_path = os.path.join(init_dir, "md-gradle-isolation.init.gradle")
    if os.path.isfile(init_path):
        return init_path

    script = r"""
def runId = System.getProperty('md.runId')
def reportsDirProp = System.getProperty('md.reportsDir')

if (runId != null && !runId.isEmpty()) {
    allprojects { p ->
        def root = gradle.rootProject.projectDir
        def safePath = p.path.replace(':','_')
        p.buildDir = new File(root, "LittleDarwinResults/gradle-build/" + runId + "/" + safePath)
    }
}

if (reportsDirProp != null && !reportsDirProp.isEmpty()) {
    allprojects { p ->
        tasks.withType(Test).configureEach { t ->
            def outDir = new File(reportsDirProp)
            outDir.mkdirs()
            // Configure JUnit XML report output location for all Gradle versions and test frameworks
            // We need to set this in multiple ways to ensure it works for JUnit, TestNG, and Spock
            try {
                // Gradle 7.4+ uses outputLocation (DirectoryProperty)
                def reportsDir = p.objects.directoryProperty()
                reportsDir.set(outDir)
                t.reports.junitXml.outputLocation.set(reportsDir)
            } catch (Throwable ignored1) {
                try {
                    // Older Gradle versions use destination (File)
                    t.reports.junitXml.destination = outDir
                } catch (Throwable ignored2) { }
            }
            // Also set in doFirst to ensure it's applied even if configuration-time setting fails
            // This is important for some test frameworks that initialize reports later
            t.doFirst {
                def reports = t.reports.junitXml
                def outDirFile = new File(reportsDirProp)
                outDirFile.mkdirs()
                try {
                    def reportsDir = p.objects.directoryProperty()
                    reportsDir.set(outDirFile)
                    reports.outputLocation.set(reportsDir)
                } catch (Throwable ignored3) {
                    try {
                        reports.destination = outDirFile
                    } catch (Throwable ignored4) { }
                }
            }
        }
    }
}
"""
    # Atomic file write: write to temp file, then rename (rename is atomic on most filesystems)
    # This prevents race conditions when multiple processes create the file in parallel
    try:
        # Use NamedTemporaryFile with delete=False, then rename
        fd, temp_path = tempfile.mkstemp(
            dir=init_dir, suffix='.gradle', prefix='.tmp-')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(script.strip() + "\n")
            # Atomic rename - if target exists, another process created it (which is fine)
            try:
                os.replace(temp_path, init_path)
            except (OSError, FileExistsError):
                # Another process created it first, remove our temp file
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
                # Double-check the file exists now
                if not os.path.isfile(init_path):
                    raise
        except Exception:
            # Clean up temp file on error
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise
    except Exception:
        # If atomic write failed, check if file was created by another process
        if os.path.isfile(init_path):
            return init_path
        raise
    return init_path


def add_gradle_test_selection_via_file(command_tokens, project_path: str, selected_tests_file: str):
    """Configure Gradle to load selected tests from a file (avoids command-length limits).

    Adds:
      - `-I <init-script>`
      - `-Dmd.includeTestsFile=<selected_tests_file>`

    Note: We intentionally do NOT use `-b/--build-file`.
    """
    init_script = ensure_gradle_test_selection_init_script(project_path)
    # IMPORTANT: Gradle init scripts and system properties must be parsed before tasks.
    # If we append them after tasks, Gradle may ignore them and run the full suite.
    out = list(command_tokens)
    if not out:
        return out
    cmd0 = out[0]
    rest = out[1:]
    injected = [cmd0, "-I", init_script,
                f"-Dmd.includeTestsFile={selected_tests_file}"]
    injected.extend(rest)
    return injected


def add_gradle_isolation(command_tokens, project_path: str, run_id: str, reports_dir: str | None = None):
    """Add Gradle per-run isolation (parallel-safe outputs).

    Adds:
      - `--no-daemon` (avoid daemon sharing across parallel runs)
      - `-I <md-gradle-isolation.init.gradle>`
      - `-Dmd.runId=<run_id>`
      - optional `-Dmd.reportsDir=<reports_dir>`
    """
    init_script = ensure_gradle_isolation_init_script(project_path)
    out = list(command_tokens)
    if not out:
        return out
    cmd0 = out[0]
    rest = out[1:]
    injected = [cmd0]
    if "--no-daemon" not in rest:
        injected.append("--no-daemon")
    injected.extend(["-I", init_script, f"-Dmd.runId={run_id}"])
    if reports_dir:
        injected.append(f"-Dmd.reportsDir={reports_dir}")
    injected.extend(rest)
    return injected


def prepare_gradle_test_command(command_tokens, project_path: str, mutant_id: str, reports_dir: str, selected_tests_file: str | None = None):
    """Prepare a complete Gradle test command with all necessary flags.

    This function combines test selection (if provided) and isolation flags
    into a single command. It's a convenience function that calls:
    - add_gradle_test_selection_via_file (if selected_tests_file is provided)
    - add_gradle_isolation (always)

    Args:
        command_tokens: Base command list (e.g., ["gradle", "test"])
        project_path: Path to the Gradle project root
        mutant_id: Unique identifier for this mutant/run
        reports_dir: Directory where test reports should be written
        selected_tests_file: Optional path to file containing selected test patterns

    Returns:
        Modified command list with all necessary flags added
    """
    out = list(command_tokens)
    # First add test selection if provided
    if selected_tests_file:
        out = add_gradle_test_selection_via_file(
            out, project_path, selected_tests_file)
    # Then add isolation flags (always needed for parallel-safe execution)
    out = add_gradle_isolation(out, project_path, str(mutant_id), reports_dir)
    return out


def change_build_file(command, new_buildFile: str):
    """Inject or replace the build file argument in a tokenized command list.

    Args:
        command: List of command tokens (e.g., from getCommand).
        new_buildFile: Path to the build file to enforce.

    Returns:
        New command list with -f/--file/-buildfile pointing to new_buildFile.
    """
    new_command = []
    i = 0
    found = False
    while i < len(command):
        new_buildFile = new_buildFile.replace("\\", "/")
        new_command.append(command[i])
        if command[i] in ["-f", "--file", "-buildfile"]:
            found = True
            i += 1
            new_command.append(new_buildFile)
        i += 1
    if not found:
        # For Gradle, do not attempt to override build file via flags.
        tool = detect_build_tool(command[0]) if command else ""
        if tool == "gradle":
            return command
        new_command.append("-f")
        new_command.append(new_buildFile)
    return new_command


def return_D_arguments(command):
    """Return -D system properties from a command string as a list of tokens."""
    args = shlex.split(command)
    D_args = []
    i = 0
    while i < len(args):
        if args[i].startswith("-D"):
            D_args.append(args[i])
        i += 1
    return D_args


def getCommand(commandString: str):
    """Convert a comma-separated command into a token list.

    Use \f to represent a literal comma.

    Args:
        commandString: The raw command string.

    Returns:
        List of command tokens suitable for subprocess execution.
    """
    placeholder = "__MD_LITERAL_COMMA__"
    preserved = commandString.replace("\f", placeholder)
    tokens = preserved.split(",")
    return [token.replace(placeholder, ",") for token in tokens]


def getAllInstantiableSubclasses(parentClass):
    """Return all instantiable subclasses of the given mutation operator base class.

    Args:
        parentClass: A `MutationOperator` subclass to search from.

    Returns:
        A set of unique subclasses that are marked instantiable.
    """
    allInstantiableSubclasses = set()
    subClasses = parentClass.__subclasses__()
    for subClass in subClasses:
        if subClass.instantiable:
            allInstantiableSubclasses.add(subClass)
        allInstantiableSubclasses.update(
            getAllInstantiableSubclasses(subClass))
    allInstantiableSubclasses.update({parentClass})
    return allInstantiableSubclasses


def parse_junit_xml(xml_file):
    """Parse a JUnit XML report into a list of test results.

    Args:
        xml_file: Path to a JUnit XML file.

    Returns:
        List of tuples: (test_name, time, failure_message, error_message).
        Returns an empty list if parsing fails.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        results = []
        for testcase in root.findall("testcase"):
            name = testcase.get("classname") + "." + testcase.get("name")
            if "(" in name:
                name = name[:name.find("(")]
            failures = testcase.findall("failure")
            failureMessage = ""
            if len(failures) > 0:
                failureMessage = failures[0].text
            errors = testcase.findall("error")
            errorMessage = ""
            if len(errors) > 0:
                errorMessage = errors[0].text
            time = testcase.get("time")
            results.append((name, time, failureMessage, errorMessage))
    except Exception as e:
        return []
    return results


def normalize_file_path(file_path: str, project_root: str = None) -> str:
    """Normalize file path to relative path from project root.

    Converts absolute paths to relative paths. If path is already relative
    or project_root is not provided, normalizes path separators only.

    Args:
        file_path: File path to normalize (can be absolute or relative)
        project_root: Optional project root directory for relative path conversion

    Returns:
        Normalized relative path with forward slashes, or original path if normalization fails
    """
    if not file_path:
        return file_path
    try:
        # Normalize path separators first
        normalized = file_path.replace("\\", "/")

        # If project_root is provided and path is absolute, make it relative
        if project_root and os.path.isabs(file_path):
            try:
                normalized = os.path.relpath(
                    file_path, project_root).replace("\\", "/")
            except (ValueError, TypeError):
                # If relpath fails (e.g., different drives on Windows), keep as-is
                pass

        return normalized
    except Exception:
        # If anything fails, return original with normalized separators
        return file_path.replace("\\", "/")


def source_relative_to_build_relative(file_path: str, source_path: str, build_path: str) -> str:
    """Convert a sourcePath-relative file path to a buildPath-relative file path.

    Args:
        file_path: File path relative to source_path (e.g. 'Triangle.java')
        source_path: The source directory (e.g. 'D:/workdir/project/src/main/java/com/example')
        build_path: The build/project root directory (e.g. 'D:/workdir/project')

    Returns:
        Path relative to build_path with forward slashes
        (e.g. 'src/main/java/com/example/Triangle.java')
    """
    if not file_path:
        return file_path
    try:
        abs_path = os.path.abspath(os.path.join(source_path, file_path))
        rel_path = os.path.relpath(abs_path, build_path)
        return rel_path.replace("\\", "/")
    except (ValueError, TypeError):
        return file_path.replace("\\", "/")


def timeoutAlternative(
    commandString,
    workingDirectory,
    timeout,
    failMessage=None,
    inputData=None,
    activeMutants=list([]), buffer_size=1024
):
    """Run a command with a hard timeout, capturing stdout and stderr.

    On timeout, attempts to terminate the process group (POSIX) or uses
    taskkill on Windows. Optionally marks active mutants via env vars.

    Args:
        commandString: List of command tokens to execute.
        workingDirectory: Directory to run the process in.
        timeout: Timeout in seconds.
        failMessage: Optional substring that, if present in output, marks failure.
        inputData: Optional data for stdin (unused).
        activeMutants: List of active mutant ids to expose as MUT* env vars.
        buffer_size: Chunk size for reading process output.

    Returns:
        Tuple (killed, return_code, combined_output, elapsed_seconds).
    """
    killCheck = threading.Event()

    # this method is run in another thread when the timeout is expired to kill the process.
    def killProcess(pipe):
        """Internal kill routine for watchdog timer."""
        assert isinstance(pipe, subprocess.Popen)

        # there is no support for os.killpg on windows, neither does it have SIGKILL.
        if platform.system() == "Windows":
            # this utility is not included in windows XP Home edition, however, there is no other alternative either.
            # therefore, don't run MediumDarwin on windows XP Home edition; he gets sad.
            subprocess.Popen("taskkill /F /T /PID %i" % pipe.pid, shell=True)
        else:
            # posix systems all support this call.
            # pipe.terminate()
            try:
                os.killpg(os.getpgid(pipe.pid), signal.SIGTERM)
            except Exception:
                os.kill(pipe.pid, signal.SIGTERM)

        # we just killed the process. let everyone know.
        killCheck.set()

    # timeout must be int, otherwise problems arise.
    assert isinstance(timeout, int)

    reliableCommandString = shutil.which(os.path.abspath(commandString[0]))

    reliableCommandString = shutil.which(os.path.abspath(os.path.join(workingDirectory, commandString[0]))) \
        if reliableCommandString is None else reliableCommandString

    reliableCommandString = shutil.which(commandString[0]) \
        if reliableCommandString is None else reliableCommandString

    if reliableCommandString is None:
        print(
            "\nBuild command not correct. Cannot find the executable: " + commandString[0])
        sys.exit(5)

    commandString[0] = reliableCommandString
    my_env = os.environ.copy()
    for activeMutant in activeMutants:
        my_env["MUT" + str(activeMutant)] = "true"
    # starting the process with the given parameters.
    if platform.system() != "Windows":
        process = subprocess.Popen(commandString, cwd=workingDirectory, stdin=subprocess.PIPE, env=my_env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    else:  # in Windows
        # Special-case Gradle .bat/.cmd on Windows:
        # dotted -D args can be mis-parsed unless quoted by cmd.exe parsing.
        tool = detect_build_tool(commandString[0]) if commandString else ""
        is_bat = str(commandString[0]).lower().endswith((".bat", ".cmd"))
        if tool == "gradle" and is_bat:
            def _q(a: str) -> str:
                if a is None:
                    return ""
                a = str(a)
                # Quote only arguments that contain whitespace. For Gradle on Windows, dotted -D args
                # work fine as long as we move them before tasks (handled below).
                if (" " in a) or ("\t" in a):
                    return f"\"{a}\""
                return a
            # Gradle on Windows is picky: system properties (-D...) must appear before tasks,
            # otherwise they may be interpreted as task selectors. Reorder them to the front.
            d_args = []
            other = []
            for a in commandString[1:]:
                if isinstance(a, str) and a.startswith("-D"):
                    d_args.append(a)
                else:
                    other.append(a)
            ordered = [commandString[0]] + d_args + other
            cmdline = " ".join([_q(ordered[0])] + [_q(a) for a in ordered[1:]])
            # Use shell=True so Windows runs the .bat via cmd.exe with correct quoting semantics.
            process = subprocess.Popen(cmdline, shell=True, cwd=workingDirectory, stdin=subprocess.PIPE, env=my_env,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            process = subprocess.Popen(commandString, cwd=workingDirectory, stdin=subprocess.PIPE, env=my_env,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    timeStarted = time.time()
    # passing the process and timeout references to threading's timer method, so that it kills the process
    # if timeout expires.
    timerWatchdog = threading.Timer(timeout, killProcess, args=[process])
    timerWatchdog.start()

    buffer_size = 1024
    output_max_reached = False
    output_max_size = 1024 * 1024 * 100  # 100MB
    output_size = 0
    # getting the output of the process.
    stdout_str = ""
    stderr_str = ""
    output = process.stdout.read(buffer_size)
    output_err = ""
    output_err = process.stderr.read(
        buffer_size) if process.stderr is not None else output_err
    while process.poll() is None or output != b"":
        if output and output_max_reached is False:
            output_size += len(output)
            # Don't strip() here - it removes whitespace/newlines needed for position calculations
            stdout_str += output.decode("utf-8", errors="ignore")
        if output_size > output_max_size:
            output_max_reached = True
        output = process.stdout.read(buffer_size)
        output_err = process.stderr.read(
            buffer_size) if process.stderr is not None else output_err
        # Don't strip() here - it removes whitespace/newlines needed for position calculations
        stderr_str += output_err.decode(
            "utf-8", errors="ignore") if output_err != "" else output_err

    process.wait()
    timerWatchdog.cancel()

    isKilled = killCheck.is_set()
    killCheck.clear()
    try:
        process.kill()
        process.terminate()
        process.wait()
    except Exception:
        print("error killing process")

    if failMessage != None:
        if failMessage in stdout_str:
            isKilled = True
    timeDelta = time.time() - timeStarted

    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    stdout_str += "\n ================================================ STDERR ================================================ \n"
    stdout_str += stderr_str
    stdout_str = ansi_escape.sub('', stdout_str)
    return isKilled, process.returncode, stdout_str, timeDelta
