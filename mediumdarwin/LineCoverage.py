"""Coverage integration helpers for Maven and Ant builds.

Provides utilities to instrument builds with Clover, run targeted tests,
and extract coverage data for guiding mutation execution and subsumption.
"""
import os
import subprocess
import xml.etree.ElementTree as ET
import re
import shutil
import json
import zipfile
import tempfile
import urllib.request
from xml.etree import ElementTree
# from importlib import resources
try:
    import importlib_resources as resources
except ModuleNotFoundError:
    from importlib import resources
from mediumdarwin.Database import Database
from mediumdarwin.SharedFunctions import timeoutAlternative
from mediumdarwin.SharedFunctions import detect_build_tool
from mediumdarwin.SharedFunctions import normalize_file_path
from pathlib import Path


class LineCoverage:
    """Manage build instrumentation and coverage extraction.

    Handles inserting Clover configuration into Maven/Ant builds, executing
    tests (optionally narrowed by coverage), and extracting coverage details
    to support mutation test selection and subsumption.
    """

    tree_clover = None
    build_type = None  # maven, ant, gradle
    timeout = None
    include_file_add = None
    runAllTests = False
    build_file_path = None
    D_args = []
    report_path = None

    def _prepare_pom(self, include_file_add=None):
        """Prepare a temporary pom.xml with coverage and include file."""
        if include_file_add == None:
            self.include_file_add = str(
                os.path.join(
                    self.project_path,
                    "LittleDarwinResults",
                    "include-tests.txt",
                )
            )
        else:
            self.include_file_add = include_file_add
        shutil.copy2(self.build_file_path, str(self.build_file_path) + ".bak")
        # Update the junit version to 4.13.2 because test exclusion is not supported in older versions
        self._update_juint_version_add_clover_pom_xml()

    def _prepare_build_xml(self, junit_target, include_file=None, subsumption=False):
        """Prepare a temporary Ant build.xml with coverage and include file."""
        if include_file == None:
            self.include_file_add = str(
                os.path.join(
                    self.project_path,
                    "LittleDarwinResults",
                    "include-tests.txt",
                )
            )
        else:
            self.include_file_add = include_file
        shutil.copy2(self.build_file_path, str(self.build_file_path) + ".bak")
        self._update_juint_version_add_clover_build_xml(
            junit_target=junit_target, subsumption=subsumption
        )

    def _prepare_gradle_clover(self):
        """Legacy: prepares a Gradle init script for OpenClover (kept for backward compatibility).

        Newer MediumDarwin versions prefer Java-agent based coverage for Gradle due to Clover DB
        instability/compatibility issues in real projects.
        """
        os.makedirs(os.path.join(self.project_path,
                    "LittleDarwinResults"), exist_ok=True)
        self.clover_db_path = str(os.path.join(
            self.project_path, "LittleDarwinResults", "clover.db"))
        init_path = os.path.join(
            self.project_path, "LittleDarwinResults", "md-clover.init.gradle")

        # Always (re)write the init script to pick up bugfixes across MediumDarwin versions.
        #
        # OpenClover manual integration via init script, based on:
        # https://openclover.org/doc/manual/latest/gradle--gradle-clover-plugin.html
        #
        # We do not depend on any Gradle Clover plugin (many are incompatible with Gradle 8+).
        # Instead we add OpenClover on the init script classpath and wire tasks similar to the doc.
        #
        # Override knobs:
        #   -Dmd.cloverVersion=<version>                     (default: 4.5.2)
        #   -Dmd.cloverDbPath=<absolute path to clover.db>   (default: <cwd>/LittleDarwinResults/clover.db)
        script = r"""
// MediumDarwin OpenClover init script (manual integration) (MD_CLOVER_MANUAL_V1)

initscript {
    repositories {
        mavenCentral()
    }
    dependencies {
        def v = System.getProperty('md.cloverVersion') ?: '4.5.2'
        classpath("org.openclover:clover:${v}")
    }
}

// NOTE: In init scripts, gradle.rootProject may not be available during script evaluation.
def mdRootDir = gradle.startParameter.currentDir
def dbPath = System.getProperty('md.cloverDbPath') ? new File(System.getProperty('md.cloverDbPath'))
    : new File(mdRootDir, 'LittleDarwinResults/clover.db')

allprojects { p ->
    p.pluginManager.withPlugin('java') {
        def ss = p.extensions.findByName('sourceSets')
        if (ss == null) { return }

        def mainSS = ss.findByName('main')
        def testSS = ss.findByName('test')
        if (mainSS == null || testSS == null) { return }

        // Create a clover source set which will compile instrumented sources.
        def cloverSS = ss.findByName('clover')
        if (cloverSS == null) {
            cloverSS = ss.create('clover')
            cloverSS.java.srcDir(p.layout.buildDirectory.dir('sources-instr').get().asFile)
        }

        // Create Clover configs similar to doc, but avoid deprecated configurations.
        def cloverCompile = p.configurations.findByName('cloverCompile')
        if (cloverCompile == null) {
            cloverCompile = p.configurations.create('cloverCompile') { cfg ->
                cfg.canBeConsumed = false
            }
        }
        def cloverRuntime = p.configurations.findByName('cloverRuntime')
        if (cloverRuntime == null) {
            cloverRuntime = p.configurations.create('cloverRuntime') { cfg ->
                cfg.canBeConsumed = false
                cfg.extendsFrom(cloverCompile)
            }
        }

        // Ensure OpenClover is available at runtime.
        try {
            def v = System.getProperty('md.cloverVersion') ?: '4.5.2'
            p.dependencies.add('cloverCompile', "org.openclover:clover:${v}")
        } catch (Throwable ignored) { }

        def instrOutDir = p.layout.buildDirectory.dir('sources-instr').get().asFile

        // Task equivalent to the doc's cloverInstr task: instrument Java sources using CloverInstr.
        def cloverInstrProvider = null
        if (p.tasks.findByName('cloverInstr') != null) {
            cloverInstrProvider = p.tasks.named('cloverInstr')
        } else {
            cloverInstrProvider = p.tasks.register('cloverInstr') { t ->
                t.group = 'verification'
                t.description = 'Instrument sources with OpenClover (generated by MediumDarwin)'
                t.inputs.files(mainSS.allJava)
                t.outputs.dir(instrOutDir)
                t.doFirst {
                    instrOutDir.mkdirs()
                    dbPath.parentFile.mkdirs()
                    def argsList = ['--initstring', dbPath.absolutePath, '-d', instrOutDir.absolutePath]
                    mainSS.allJava.files.each { f -> argsList.add(f.absolutePath) }
                    String[] args = argsList.toArray(new String[0])
                    com.atlassian.clover.CloverInstr.mainImpl(args)
                }
            }
        }

        // Ensure instrumented sources are compiled before tests.
        try {
            p.tasks.named('cloverClasses').configure { it.dependsOn(cloverInstrProvider) }
        } catch (Throwable ignored2) { }
        try {
            p.tasks.named('test').configure { it.dependsOn(cloverInstrProvider) }
        } catch (Throwable ignored3) { }

        // Make sure the clover SourceSet can compile:
        // - instrumented sources reference com_atlassian_clover.* (needs Clover on the compile classpath)
        // - project code may reference dependencies (reuse main compile/runtime classpaths)
        try {
            cloverSS.compileClasspath = cloverSS.compileClasspath + mainSS.compileClasspath + cloverCompile
        } catch (Throwable ignored4a) { }
        try {
            cloverSS.runtimeClasspath = cloverSS.runtimeClasspath + mainSS.runtimeClasspath + cloverRuntime
        } catch (Throwable ignored4b) { }

        // Gradle 8 task validation: explicitly wire Clover compilation to cloverInstr output.
        // SourceSet 'clover' creates compile tasks like compileCloverJava/compileCloverGroovy.
        p.tasks.matching { it.name.toLowerCase().startsWith('compileclover') }.configureEach { t ->
            try { t.dependsOn(cloverInstrProvider) } catch (Throwable ignored5a) { }
            try { t.inputs.dir(instrOutDir) } catch (Throwable ignored5b) { }
            // Ensure Clover classes are on the compiler classpath so com_atlassian_clover.* resolves.
            try { t.classpath = t.classpath + cloverCompile } catch (Throwable ignored5c) { }
        }
        // And make test depend on Clover compilation so instrumented classes exist.
        try { p.tasks.named('test').configure { it.dependsOn('compileCloverJava') } } catch (Throwable ignored6) { }

        // Configure tests to run against instrumented classes, and include clover runtime.
        p.tasks.withType(Test).configureEach { t ->
            t.doFirst { dbPath.parentFile.mkdirs() }
            try {
                // Replace main output with clover output to ensure instrumented code is executed.
                def cp = t.classpath
                try { cp = cp - mainSS.output } catch (Throwable ignored7) { }
                cp = cp + cloverSS.output + cloverRuntime
                t.classpath = cp
            } catch (Throwable ignored8) { }
        }

        // Report task similar to doc; optional, but it also validates DB existence.
        if (p.tasks.findByName('cloverReport') == null) {
            p.tasks.register('cloverReport') { t ->
                t.group = 'verification'
                t.description = 'Generate OpenClover report (generated by MediumDarwin)'
                t.dependsOn('test')
                t.onlyIf { dbPath.exists() }
                t.doFirst {
                    def outDir = new File(p.buildDir, 'reports/clover')
                    outDir.mkdirs()
                    def argsList = ['--initstring', dbPath.absolutePath, '-o', outDir.absolutePath]
                    String[] args = argsList.toArray(new String[0])
                    com.atlassian.clover.reporters.html.HtmlReporter.runReport(args)
                }
            }
        }
    }
}
"""
        with open(init_path, "w", encoding="utf-8") as f:
            f.write(script.strip() + "\n")
        return init_path

    def _ensure_java_tracer_agent_jar(self) -> str:
        """Build a fat coverage-only Java agent jar from MediumDarwin's JavaTracerAgent.java (includes ASM classes).

        Output: <project>/LittleDarwinResults/jar/java-tracer-agent.jar
        """
        out_dir = os.path.join(self.project_path, "LittleDarwinResults", "jar")
        os.makedirs(out_dir, exist_ok=True)
        jar_path = os.path.join(out_dir, "java-tracer-agent.jar")

        # Prefer MediumDarwin's bundled coverage-only agent source.
        agent_src = os.path.join(
            os.path.dirname(__file__),
            "java_tracer",
            "JavaTracerAgent.java",
        )
        if not os.path.isfile(agent_src):
            agent_src = os.path.join(
                os.getcwd(),
                "mutation_research_private",
                "dmsg_homs",
                "scripts",
                "java_tracer",
                "JavaTracerAgent.java",
            )
        if not os.path.isfile(agent_src):
            raise FileNotFoundError(
                f"Java tracer agent source not found at {agent_src}. "
                "Expected mediumdarwin/java_tracer/JavaTracerAgent.java."
            )

        if os.path.isfile(jar_path):
            try:
                src_mtime = os.path.getmtime(agent_src)
                jar_mtime = os.path.getmtime(jar_path)
                if jar_mtime >= src_mtime:
                    return jar_path
            except Exception:
                return jar_path

        asm_version = "9.9"
        asm_jar = os.path.join(out_dir, f"asm-{asm_version}.jar")
        asm_tree_jar = os.path.join(out_dir, f"asm-tree-{asm_version}.jar")

        def _download(url: str, dest: str):
            if os.path.isfile(dest):
                return
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with urllib.request.urlopen(url, timeout=60) as r:
                data = r.read()
            with open(dest, "wb") as f:
                f.write(data)

        _download(
            f"https://repo1.maven.org/maven2/org/ow2/asm/asm/{asm_version}/asm-{asm_version}.jar",
            asm_jar,
        )
        _download(
            f"https://repo1.maven.org/maven2/org/ow2/asm/asm-tree/{asm_version}/asm-tree-{asm_version}.jar",
            asm_tree_jar,
        )

        javac = shutil.which("javac")
        if not javac:
            raise RuntimeError(
                "javac not found on PATH; required to build JavaTracerAgent.jar")

        build_dir = tempfile.mkdtemp(prefix="md_java_tracer_")
        try:
            cp = os.pathsep.join([asm_jar, asm_tree_jar])
            # Compile the agent for broad runtime compatibility.
            # Many Gradle test JVMs run on Java 8/11/17, while the developer machine may have newer javac.
            # Prefer --release (JDK9+); fall back to -source/-target.
            compile_cmd = [javac, "--release", "8",
                           "-cp", cp, "-d", build_dir, agent_src]
            proc = subprocess.run(compile_cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                compile_cmd = [javac, "-source", "8", "-target", "8",
                               "-cp", cp, "-d", build_dir, agent_src]
                proc = subprocess.run(
                    compile_cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(
                    "Failed to compile JavaTracerAgent.java\n"
                    + proc.stdout
                    + "\n"
                    + proc.stderr
                )

            manifest = (
                "Manifest-Version: 1.0\n"
                "Premain-Class: JavaTracerAgent\n"
                "Can-Redefine-Classes: true\n"
                "Can-Retransform-Classes: true\n"
                "\n"
            )

            def _add_asm_classes(zout: zipfile.ZipFile, asm_path: str):
                with zipfile.ZipFile(asm_path, "r") as zin:
                    for info in zin.infolist():
                        name = info.filename
                        if not name.endswith(".class"):
                            continue
                        # Only include ASM packages (avoid META-INF noise)
                        if not (name.startswith("org/objectweb/asm/")):
                            continue
                        zout.writestr(name, zin.read(name))

            with zipfile.ZipFile(jar_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("META-INF/MANIFEST.MF", manifest)
                # compiled agent classes
                for root, _, files in os.walk(build_dir):
                    for fn in files:
                        if not fn.endswith(".class"):
                            continue
                        abs_p = os.path.join(root, fn)
                        rel_p = os.path.relpath(
                            abs_p, build_dir).replace(os.sep, "/")
                        z.write(abs_p, rel_p)
                # embed ASM
                _add_asm_classes(z, asm_jar)
                _add_asm_classes(z, asm_tree_jar)

            return jar_path
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)

    def _prepare_gradle_java_tracer(self, agent_jar: str, trace_file: str, coverage_file: str) -> str:
        """Write a Gradle init script that injects JavaTracerAgent via -javaagent into all Test tasks.

        NOTE (Windows Gradle CLI): passing dotted `-Dmd.*` properties via the command line can be
        mis-parsed as task selectors unless carefully quoted. To keep this robust across shells,
        we embed the resolved paths directly into the init script.

        This function is parallel-safe: uses atomic file writing to avoid race conditions.
        """
        init_dir = os.path.join(self.project_path, "LittleDarwinResults")
        os.makedirs(init_dir, exist_ok=True)
        init_path = os.path.join(init_dir, "md-java-tracer.init.gradle")

        # Fast path: if file already exists, return it (another process may have created it)
        if os.path.isfile(init_path):
            return init_path

        # Use absolute project root in agent args for source-file resolution.
        # Args format (per JavaTracerAgent): outputFile@@projectRoot@@coverageFile
        # Note: JavaTracerAgent expects paths as-is; Gradle will pass this string to the JVM.
        # Embed resolved paths here to avoid Windows CLI parsing quirks for dotted -D properties.
        agent_jar_g = agent_jar.replace("\\", "/")
        trace_file_g = trace_file.replace("\\", "/")
        coverage_file_g = coverage_file.replace("\\", "/")
        root_dir_g = self.project_path.replace("\\", "/")

        script = f"""
// MediumDarwin JavaTracerAgent init script (MD_JAVA_TRACER_V2_EMBEDDED_PATHS)
allprojects {{ p ->
  tasks.withType(Test).configureEach {{ t ->
    def agentJar = "{agent_jar_g}"
    def traceOut = "{trace_file_g}"
    def covOut = "{coverage_file_g}"
    def rootDir = "{root_dir_g}"
    // Ensure the test task actually runs, otherwise the agent never executes and produces no JSON.
    try {{ t.outputs.upToDateWhen {{ false }} }} catch (Throwable ignored) {{ }}
    t.jvmArgs("-javaagent:${{agentJar}}=${{traceOut}}@@${{rootDir}}@@${{covOut}}")
  }}
}}
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

    def _import_java_tracer_coverage_to_db(self, coverage_json_path: str) -> None:
        """Import JavaTracerAgent coverage JSON into MediumDarwin SQLite schema.

        Populates:
          - test (qualified_name)
          - test_coverage (file_id, line_no, test_id)
        """
        if not os.path.isfile(coverage_json_path):
            raise FileNotFoundError(
                f"Coverage JSON not found: {coverage_json_path}")

        with open(coverage_json_path, "r", encoding="utf-8") as f:
            cov = json.load(f)

        files_cov = cov.get("files", {})
        if not isinstance(files_cov, dict):
            raise ValueError("Invalid coverage JSON: missing 'files' object")

        # Use Database class methods instead of direct SQL
        db = Database(self.sqlDB_path)
        try:
            # Ensure tables exist (do not touch mutation tables here)
            db.create_table(
                "test", "id INTEGER PRIMARY KEY, qualified_name TEXT")
            db.create_table("test_coverage",
                            "file_id INTEGER, line_no INTEGER, test_id TEXT")
            db.create_table(
                "file", "name TEXT, id INTEGER PRIMARY KEY, json TEXT")

            # Ensure special placeholder tests exist (needed for JOINs in Database.fetch_coverage).
            # Without these, rows like test_id = Database.INSTURMENTED_NOT_COVERED (-2) may not be visible via JOIN.
            db.ensure_test_placeholders()

            # Clear old coverage mappings (keep tests/files)
            db.clear_test_coverage()

            # Cache existing tests by qualified_name
            test_map = db.get_all_tests_dict()

            def _normalize_test_name(t: str) -> str:
                # JavaTracerAgent uses internal name + ":" + method, e.g. a/b/C:testMethod
                if ":" in t:
                    cls, meth = t.split(":", 1)
                    cls = cls.replace("/", ".")
                    return f"{cls}.{meth}"
                return t.replace("/", ".")

            def _get_or_create_test_id(name: str) -> int:
                # Do not insert unknown test placeholders; map to NO_INFO instead.
                if not name or name.strip().lower() == "unknown":
                    return Database.NO_INFO
                if name in test_map:
                    return test_map[name]
                tid = db.get_or_create_test_id(name)
                test_map[name] = tid
                return tid

            # Create a minimal options object for path normalization if source_path is available
            options_obj = None
            if self.source_path:
                class Options:
                    pass
                options_obj = Options()
                options_obj.buildPath = self.project_path
                options_obj.sourcePath = self.source_path

            inserts = []
            for file_key, fobj in files_cov.items():
                if not isinstance(fobj, dict):
                    continue
                file_id = db.get_file_id_with_fallback(
                    file_key, options=options_obj)
                stmts = fobj.get("statements", [])
                if not isinstance(stmts, list):
                    continue

                for st in stmts:
                    if not isinstance(st, dict):
                        continue
                    line_no = st.get("line_number")
                    if not isinstance(line_no, int):
                        continue
                    tests = st.get("covered_by_tests", []) or []
                    if tests:
                        for tname in tests:
                            if not isinstance(tname, str) or not tname:
                                continue
                            tid = _get_or_create_test_id(
                                _normalize_test_name(tname))
                            inserts.append((file_id, line_no, tid))
                    else:
                        inserts.append(
                            (file_id, line_no, Database.INSTURMENTED_NOT_COVERED))

            # Insert coverage data from trace_coverage.json into the database
            if inserts:
                db.insert_test_coverage_bulk(inserts)
            else:
                summary = cov.get("summary", {})
                raise RuntimeError(
                    "JavaTracerAgent produced no statement coverage entries to import into SQLite. "
                    f"coverage_json={coverage_json_path} files={len(files_cov)} summary={summary}. "
                    "This usually means the agent did not instrument project classes or debug line numbers were missing."
                )
        finally:
            db.close_connection()

    def backfill_mutation_coverage(self, options=None) -> None:
        """Backfill coverage for mutation lines that do not appear in the tracer JSON.

        This should be called AFTER mutations have been inserted into the database.
        This handles the case where a source file has mutants but *no tests load/execute* its classes,
        so the tracer never observes any statements for that file. We still need DB entries so the
        mutation runner can tell the difference between "no tests cover this line" and "missing data".

        Args:
            options: Options object with buildPath and sourcePath (optional, for path normalization)
        """
        db = Database(self.sqlDB_path)
        try:
            # Get all mutated lines directly by file_id - this is the source of truth
            # This bypasses path normalization issues and ensures we catch all files with mutations
            mutated_lines_by_file_id = db.get_mutated_lines_by_file_id()

            if not mutated_lines_by_file_id:
                # No mutations in database yet, nothing to backfill
                return

            # Get existing coverage from database
            existing_coverage = db.get_existing_test_coverage()

            # Backfill all mutated lines that aren't in existing coverage
            backfill = []
            for file_id, line_no in mutated_lines_by_file_id:
                key = (int(file_id), int(line_no))
                if key in existing_coverage:
                    continue
                # The file/line has mutations but was not observed by the tracer output at all.
                # Treat as instrumented-but-not-covered so downstream logic sees the '-' marker.
                backfill.append(
                    (file_id, line_no, Database.INSTURMENTED_NOT_COVERED))

            # Insert backfill entries
            if backfill:
                db.insert_test_coverage_bulk(backfill)

            # Final verification: ensure ALL mutations have coverage entries
            # This catches any edge cases where file_ids might not match due to path issues
            missing_after_insert = db.verify_mutation_coverage_completeness()
            if missing_after_insert:
                # If there are still missing entries, add them
                additional_backfill = []
                for file_id, line_no in missing_after_insert:
                    additional_backfill.append(
                        (file_id, line_no, Database.INSTURMENTED_NOT_COVERED))
                if additional_backfill:
                    db.insert_test_coverage_bulk(additional_backfill)
        finally:
            db.close_connection()

    def _merge_pid_coverage_files(self, base_coverage_file: str) -> None:
        """Merge all per-process coverage files (trace_coverage.<pid>.json) into base file.

        Args:
            base_coverage_file: Path to the base coverage file (e.g., trace_coverage.json)
        """
        base_path = Path(base_coverage_file)
        if not base_path.parent.exists():
            return

        # Find all PID files matching the pattern: trace_coverage.<pid>.json
        base_name = base_path.name  # e.g., "trace_coverage.json"
        stem = base_name.rsplit(".json", 1)[0] if base_name.endswith(
            ".json") else base_name

        pid_files = []
        for f in base_path.parent.iterdir():
            if f.is_file() and f.name.startswith(stem + ".") and f.name.endswith(".json"):
                # Check if it's a PID file (not the base file itself)
                if f.name != base_name:
                    # Verify it matches pattern: stem.<pid>.json
                    # Extract the middle part between stem. and .json
                    prefix_len = len(stem) + 1  # +1 for '.'
                    if len(f.name) > prefix_len + 5:  # Need at least ".json" (5 chars)
                        # Extract part between stem. and .json
                        middle = f.name[prefix_len:-5]
                        # Check if middle is numeric (allows dots for PIDs like "12345.67890")
                        if middle and (middle.isdigit() or (middle.replace(".", "").isdigit() and middle.count(".") <= 1)):
                            pid_files.append(f)

        if not pid_files:
            return

        # Merge all PID files into a single coverage map
        merged_coverage = {}

        for pid_file in pid_files:
            try:
                with open(pid_file, "r", encoding="utf-8") as f:
                    pid_data = json.load(f)

                files_cov = pid_data.get("files", {})
                if not isinstance(files_cov, dict):
                    continue

                # Merge coverage data: for each file, merge statements
                for file_key, file_obj in files_cov.items():
                    if not isinstance(file_obj, dict):
                        continue

                    if file_key not in merged_coverage:
                        merged_coverage[file_key] = {"statements": []}

                    stmts = file_obj.get("statements", [])
                    if not isinstance(stmts, list):
                        continue

                    # Create a map of existing statements by (line_number, class_name, method_name)
                    existing_map = {}
                    for stmt in merged_coverage[file_key]["statements"]:
                        if isinstance(stmt, dict):
                            key = (
                                stmt.get("line_number"),
                                stmt.get("class_name"),
                                stmt.get("method_name")
                            )
                            if key[0] is not None:
                                existing_map[key] = stmt

                    # Merge new statements
                    for stmt in stmts:
                        if not isinstance(stmt, dict):
                            continue
                        key = (
                            stmt.get("line_number"),
                            stmt.get("class_name"),
                            stmt.get("method_name")
                        )
                        if key[0] is None:
                            continue

                        if key in existing_map:
                            # Merge tests: combine covered_by_tests sets
                            existing_tests = set(
                                existing_map[key].get("covered_by_tests", []))
                            new_tests = set(stmt.get("covered_by_tests", []))
                            existing_map[key]["covered_by_tests"] = sorted(
                                list(existing_tests | new_tests))
                        else:
                            # Add new statement
                            existing_map[key] = stmt.copy()
                            if "covered_by_tests" in existing_map[key]:
                                existing_map[key]["covered_by_tests"] = sorted(
                                    existing_map[key]["covered_by_tests"])

                    # Update statements list
                    merged_coverage[file_key]["statements"] = sorted(
                        existing_map.values(),
                        key=lambda s: (s.get("line_number", 0), s.get(
                            "class_name", ""), s.get("method_name", ""))
                    )
            except Exception as e:
                # Log but continue with other files
                print(f"Warning: Failed to merge PID file {pid_file}: {e}")
                continue

        # Write merged coverage to base file
        if merged_coverage:
            merged_json = {"files": merged_coverage}
            with open(base_path, "w", encoding="utf-8") as f:
                json.dump(merged_json, f, indent=2, ensure_ascii=False)

            # Remove PID files after successful merge
            for pid_file in pid_files:
                try:
                    pid_file.unlink()
                except Exception as e:
                    print(
                        f"Warning: Failed to remove PID file {pid_file}: {e}")

            # Remove lock file if it exists (leftover from old Java merging logic)
            lock_file = base_path.parent / (base_name + ".lock")
            if lock_file.exists():
                try:
                    lock_file.unlink()
                except Exception as e:
                    print(
                        f"Warning: Failed to remove lock file {lock_file}: {e}")

    # NOTE: merging of per-process JavaTracerAgent coverage JSON files is now handled
    # in Python (writes trace_coverage.<pid>.json and merges into trace_coverage.json).

    def _clean_clover_from_build_xml(self, junit_target):
        """Remove Clover customizations from Ant build.xml and restore header."""
        with open(self.build_file_path, "r") as f:
            data = f.read()
        data = data.replace("&test_file_for_clover", "test_file_for_clover")
        with open(self.build_file_path, "w") as f:
            f.write(data)

        tree = ET.parse(self.build_file_path)
        root = tree.getroot()
        os.chdir(self.project_path)

        root.remove(root.find('./taskdef[@resource="cloverlib.xml"]'))
        root.remove(root.find('./property[@name="clover.jar"]'))

        test_target_element = root.find(".//*[@name='" + junit_target + "']")
        junit_element = test_target_element.find(".//junit")

        for formatter in junit_element.findall(".//formatter"):
            junit_element.remove(formatter)

        tree.write(self.build_file_path)
        header = (
            '<?xml version="1.0"?><!DOCTYPE project [<!ENTITY test_file_for_clover SYSTEM "'
            + self.include_file_add
            + '">]>'
        )
        with open(self.build_file_path, "r") as f:
            data = f.read()
        data = data.replace("test_file_for_clover", "&test_file_for_clover")
        with open(self.build_file_path, "w") as f:
            f.write(header + data)

    def add_tests_to_pom_xml(
        self, include_tests_file, report_path, covered_tests=[], subsumption=None
    ):
        """Configure Surefire to run only tests listed in include file.

        Writes the include list and configures report directory.
        """
        # Only write to include file if test selection is enabled
        if self.runAllTests == False:
            with open(include_tests_file, "w") as f:
                for test_name in covered_tests:
                    if test_name != "":
                        test_name = test_name[0]  # tuple to string
                        # test_name = test_name.split(".")
                        # test_name = test_name[-2] + "#" + test_name[-1]
                    f.write(test_name + "\n")
        shutil.rmtree(report_path, ignore_errors=True)
        os.makedirs(report_path, exist_ok=True)

        # ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
        tree = ET.parse(self.build_file_path)
        root = tree.getroot()
        namespace = self.return_namespace(root)
        ET.register_namespace("", namespace)
        # Find the <build> element
        for build_element in root.findall(f"{{{namespace}}}build"):
            if build_element is None:
                build_element = ElementTree.SubElement(root, "build")
            # Find or create the <plugins> element
            plugins_element = build_element.find(
                f"{{{namespace}}}plugins"
            )
            if plugins_element is None:
                plugins_element = ElementTree.SubElement(
                    build_element, "plugins")
            plugins = plugins_element.findall(
                f"{{{namespace}}}plugin"
            )
            for plugin in plugins:
                artifactId = plugin.find(
                    f"{{{namespace}}}artifactId",
                )

                if (
                    artifactId is not None
                    and artifactId.text == "maven-surefire-plugin"
                ):
                    configuration_element = plugin.find(
                        f"{{{namespace}}}configuration"
                    )
                    if configuration_element is None:
                        configuration_element = ElementTree.SubElement(
                            plugin, "configuration"
                        )

                    if self.runAllTests == False:
                        skip_after_failure_element = configuration_element.find(
                            f".//{{{namespace}}}skipAfterFailureCount"
                        )
                        if skip_after_failure_element == None:
                            skip_after_failure_element = ElementTree.SubElement(
                                configuration_element, "skipAfterFailureCount"
                            )
                        # Surefire uses skipAfterFailureCount=1 to stop on the first failure.
                        skip_after_failure_element.text = "1"

                        includes_file_element = configuration_element.find(
                            f".//{{{namespace}}}includesFile"
                        )
                        if includes_file_element == None:
                            includes_file_element = ElementTree.SubElement(
                                configuration_element, "includesFile"
                            )
                        includes_file_element.text = self.include_file_add

                    reportsDirectory = configuration_element.find(
                        f"{{{namespace}}}reportsDirectory",
                    )
                    if reportsDirectory is None:
                        reportsDirectory = ElementTree.SubElement(
                            configuration_element, "reportsDirectory"
                        )
                    reportsDirectory.text = str(report_path)

        # Save the modified pom.xml file
        tree.write(self.build_file_path)

    def add_tests_to_build_xml(
        self, junit_target, report_path, covered_tests=None, subsumption=False
    ):
        """Inject tests into Ant build target and write include file."""
        if covered_tests is None:
            covered_tests = []
        os.chdir(self.project_path)
        shutil.rmtree(report_path, ignore_errors=True)
        os.makedirs(report_path, exist_ok=True)

        # Only write to include file if test selection is enabled
        if self.runAllTests == False:
            data_dump = ""
            for test in covered_tests:
                test = test[0]  # tuple to string

                ind = test.rfind("#")
                test_element = ET.Element("test")
                test_element.set("name", test[:ind])
                test_element.set("methods", test[ind + 1:])
                if subsumption:
                    os.makedirs(os.path.join(report_path, test), exist_ok=True)
                    test_element.set(
                        "todir",
                        os.path.join(report_path, test),
                    )
                data_dump += ET.tostring(test_element).decode("utf-8") + "\n"
            with open(
                self.include_file_add,
                "w",
            ) as f:
                f.write(data_dump)

    def _update_juint_version_add_clover_build_xml(
        self, junit_target, subsumption=False
    ):
        """Update Ant build.xml to use JUnit 4.13.2 and add Clover hooks."""

        tree = ET.parse(self.build_file_path)
        root = tree.getroot()
        os.chdir(self.project_path)
        with resources.as_file(
            resources.files("mediumdarwin").joinpath(
                "jar").joinpath("clover.jar")
        ) as clover_file_path:
            with open(clover_file_path, "rb") as clover_file:
                new_file_path = str(
                    os.path.join(
                        self.project_path, "LittleDarwinResults", "jar", "clover.jar"
                    )
                )
                os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                with open(new_file_path, "wb") as new_file:
                    new_file.write(clover_file.read())
        with resources.as_file(
            resources.files("mediumdarwin").joinpath(
                "jar").joinpath("junit-4.13.2.jar")
        ) as clover_file_path:
            with open(clover_file_path, "rb") as clover_file:
                new_file_path = str(
                    os.path.join(
                        self.project_path,
                        "LittleDarwinResults",
                        "jar",
                        "junit-4.13.2.jar",
                    )
                )
                os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                with open(new_file_path, "wb") as new_file:
                    new_file.write(clover_file.read())
        with resources.as_file(
            resources.files("mediumdarwin").joinpath(
                "jar").joinpath("hamcrest-2.2.jar")
        ) as clover_file_path:
            with open(clover_file_path, "rb") as clover_file:
                new_file_path = str(
                    os.path.join(
                        self.project_path,
                        "LittleDarwinResults",
                        "jar",
                        "hamcrest-2.2.jar",
                    )
                )
                os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                with open(new_file_path, "wb") as new_file:
                    new_file.write(clover_file.read())

        property_element = ElementTree.Element("taskdef")
        property_element.set("resource", "cloverlib.xml")
        property_element.set("classpath", "${clover.jar}")
        root.insert(0, property_element)

        property_element = ElementTree.Element("property")
        property_element.set("name", "clover.jar")
        property_element.set(
            "location",
            str(
                os.path.join(
                    self.project_path, "LittleDarwinResults", "jar", "clover.jar"
                )
            ),
        )
        root.insert(0, property_element)

        property_element = ElementTree.Element("property")
        property_element.set("name", "hamcrest-2.2.jar")
        property_element.set(
            "location",
            str(
                os.path.join(
                    self.project_path, "LittleDarwinResults", "jar", "hamcrest-2.2.jar"
                )
            ),
        )
        root.insert(0, property_element)

        property_element = ElementTree.Element("property")
        property_element.set("name", "junit-4.13.2.jar")
        property_element.set(
            "location",
            str(
                os.path.join(
                    self.project_path, "LittleDarwinResults", "jar", "junit-4.13.2.jar"
                )
            ),
        )

        root.insert(0, property_element)

        classpath_element = ElementTree.Element("classpath")
        pathelement_element = ElementTree.SubElement(
            classpath_element, "pathelement")
        pathelement_element.set("location", "build/classes")
        pathelement_element = ElementTree.SubElement(
            classpath_element, "pathelement")
        pathelement_element.set("location", "${junit-4.13.2.jar}")

        classpath_clover = ElementTree.Element("classpath")
        pathelement_element = ElementTree.SubElement(
            classpath_clover, "pathelement")
        pathelement_element.set("location", "${clover.jar}")

        classpath_hamcrest = ElementTree.Element("classpath")
        pathelement_element = ElementTree.SubElement(
            classpath_hamcrest, "pathelement")
        pathelement_element.set("location", "${hamcrest-2.2.jar}")

        test_target_element = root.find(".//*[@name='" + junit_target + "']")
        junit_element = test_target_element.find(".//junit")
        #! throw an error if junit element is not found
        # add classpath, clover and hamcrest to junit element
        if self.runAllTests:
            junit_element.set("haltonfailure", "no")
            junit_element.set("haltonerror", "no")
        else:
            junit_element.set("haltonfailure", "yes")
            junit_element.set("haltonerror", "yes")
        junit_element.insert(0, classpath_element)
        junit_element.insert(0, classpath_hamcrest)
        junit_element.insert(0, classpath_clover)

        target_with_clover = ElementTree.SubElement(root, "target")
        target_with_clover.set("name", "with.clover.mediumdarwin")
        taskdef_element = ElementTree.SubElement(target_with_clover, "taskdef")
        taskdef_element.set("resource", "cloverlib.xml")
        taskdef_element.set("classpath", "${clover.jar}")
        clover_setup_element = ElementTree.SubElement(
            target_with_clover, "clover-setup"
        )
        clover_setup_element.set(
            "initstring",
            str(os.path.join(self.project_path, "LittleDarwinResults", "clover.db")),
        )

        test_target_element = root.find(".//*[@name='" + junit_target + "']")
        junit_element = test_target_element.find(".//junit")

        # Only modify junit element to use include file if test selection is enabled
        if self.runAllTests == False:
            dump = junit_element.text

            # remove all batchtest elements
            for batchtest in junit_element.findall(".//batchtest"):
                dump += ET.tostring(batchtest).decode("utf-8")
                junit_element.remove(batchtest)

            # remove all test elements
            for test_tag in junit_element.findall(".//test"):
                dump += ET.tostring(test_tag).decode("utf-8")
                junit_element.remove(test_tag)

            # add a line of text
            junit_element.text = junit_element.text + "test_file_for_clover;"

            for formatter in junit_element.findall(".//formatter"):
                junit_element.remove(formatter)
            if subsumption:
                formatter_element = ElementTree.SubElement(
                    junit_element, "formatter")
                formatter_element.set("type", "xml")
            else:
                formatter_element = ElementTree.SubElement(
                    junit_element, "formatter")
                formatter_element.set("type", "plain")
                formatter_element.set("usefile", "false")

            tree.write(self.build_file_path)
            # write this header to the file
            header = (
                '<?xml version="1.0"?><!DOCTYPE project [<!ENTITY test_file_for_clover SYSTEM "'
                + self.include_file_add
                + '">]>'
            )
            with open(self.build_file_path, "r") as f:
                data = f.read()
            data = data.replace("test_file_for_clover",
                                "&test_file_for_clover")
            with open(self.build_file_path, "w") as f:
                f.write(header + data)

            with open(
                self.include_file_add,
                "w",
            ) as f:
                f.write(dump)
        else:
            # When runAllTests is True, just set formatter without modifying test selection
            for formatter in junit_element.findall(".//formatter"):
                junit_element.remove(formatter)
            if subsumption:
                formatter_element = ElementTree.SubElement(
                    junit_element, "formatter")
                formatter_element.set("type", "xml")
            else:
                formatter_element = ElementTree.SubElement(
                    junit_element, "formatter")
                formatter_element.set("type", "plain")
                formatter_element.set("usefile", "false")

            tree.write(self.build_file_path)

    def return_namespace(self, element):
        """Return the XML namespace of the given element tag."""
        m = re.match(r'\{(.*)\}', element.tag)
        return m.group(1) if m else ''

    def _update_juint_version_add_clover_pom_xml(self):
        """Update pom.xml to use required plugin versions and add Clover."""
        # ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
        tree = ET.parse(self.build_file_path)
        root = tree.getroot()
        namespace = self.return_namespace(root)
        ET.register_namespace("", namespace)

        # update junit version
        junit_exists = False
        for dependency in root.findall(
            f".//{{{namespace}}}dependency"
        ):
            artifact_id = dependency.find(
                f"{{{namespace}}}artifactId"
            ).text
            if artifact_id == "junit":
                junit_exists = True
                version = dependency.find(
                    f"{{{namespace}}}version"
                )
                if version is None:
                    version = ET.SubElement(
                        dependency, f"{{{namespace}}}version"
                    )
                    version.text = "4.13.2"
                version = version.text
                if version <= "4.13.2":
                    dependency.find(
                        f"{{{namespace}}}version"
                    ).text = "4.13.2"
            if artifact_id == "junit-jupiter-engine":
                junit_exists = True
        if not junit_exists:
            dependencies = root.find(
                f".//{{{namespace}}}dependencies"
            )
            if dependencies is None:
                dependencies = ET.SubElement(
                    root, f"{{{namespace}}}dependencies"
                )
            junit_dependency = ET.SubElement(
                dependencies, f"{{{namespace}}}dependency"
            )
            ET.SubElement(
                junit_dependency, f"{{{namespace}}}groupId"
            ).text = "junit"
            ET.SubElement(
                junit_dependency, f"{{{namespace}}}artifactId"
            ).text = "junit"
            ET.SubElement(
                junit_dependency, f"{{{namespace}}}version"
            ).text = "4.13.2"

        # check if a build element exists
        build_element = root.find(f"{{{namespace}}}build")
        if build_element is None:
            build_element = ET.SubElement(
                root, f"{{{namespace}}}build"
            )
        # Find the <build> element
        for build_element in root.findall(f"{{{namespace}}}build"):
            if build_element is None:
                build_element = ElementTree.SubElement(root, "build")
            # Find or create the <plugins> element
            plugins_element = build_element.find(
                f"{{{namespace}}}plugins"
            )
            if plugins_element is None:
                plugins_element = ElementTree.SubElement(
                    build_element, "plugins")

            no_surefire = True
            no_compiler = True
            # Search for the surefire plugin
            for plugin in plugins_element.findall(
                f".//{{{namespace}}}plugin"
            ):
                artifact_id = plugin.find(
                    f".//{{{namespace}}}artifactId"
                )
                if (
                    artifact_id is not None
                    and artifact_id.text == "maven-compiler-plugin"
                ):
                    no_compiler = False
                    configuration_element = plugin.find(
                        f".//{{{namespace}}}configuration"
                    )
                    source_element = configuration_element.find(
                        f".//{{{namespace}}}source"
                    )
                    if source_element is None:
                        source_element = ElementTree.SubElement(
                            configuration_element, "source"
                        )
                    source_element.text = "1.8"
                    target_element = configuration_element.find(
                        f".//{{{namespace}}}target"
                    )
                    if target_element is None:
                        target_element = ElementTree.SubElement(
                            configuration_element, "target"
                        )
                    target_element.text = "1.8"
                    # update version
                    version = plugin.find(
                        f"{{{namespace}}}version")
                    if version is None:
                        version = ElementTree.SubElement(plugin, "version")
                    version.text = "3.8.1"

                if artifact_id != None and artifact_id.text == "maven-surefire-plugin":
                    no_surefire = False
                    # Create a new <plugin> element for the surefire plugin
                    plugin_surefire_element = plugin
                    # Add the necessary child elements to the <plugin> element
                    version_element = plugin_surefire_element.find(
                        f".//{{{namespace}}}version"
                    )
                    if version_element == None:
                        version_element = ElementTree.SubElement(
                            plugin_surefire_element, "version"
                        )
                    version_element.text = "3.0.0"
                    configuration_element = plugin_surefire_element.find(
                        f".//{{{namespace}}}configuration"
                    )
                    if configuration_element == None:
                        configuration_element = ElementTree.SubElement(
                            plugin_surefire_element, "configuration"
                        )
                    if self.runAllTests == False:
                        skip_after_failure_element = configuration_element.find(
                            f".//{{{namespace}}}skipAfterFailureCount"
                        )
                        if skip_after_failure_element == None:
                            skip_after_failure_element = ElementTree.SubElement(
                                configuration_element, "skipAfterFailureCount"
                            )
                        # Surefire uses skipAfterFailureCount=1 to stop on the first failure.
                        skip_after_failure_element.text = "1"

                        includes_file_element = configuration_element.find(
                            f".//{{{namespace}}}includesFile"
                        )
                        if includes_file_element == None:
                            includes_file_element = ElementTree.SubElement(
                                configuration_element, "includesFile"
                            )

                        includes_file_element.text = self.include_file_add
                    report_element = configuration_element.find(
                        f".//{{{namespace}}}reportsDirectory"
                    )
                    if report_element == None:
                        report_element = ElementTree.SubElement(
                            configuration_element, "reportsDirectory"
                        )
                    report_element.text = str(
                        os.path.join(
                            self.project_path, "LittleDarwinResults", "test-reports"
                        )
                    )
            if no_surefire:
                # Create a new <plugin> element for the surefire plugin
                plugin_surefire_element = ElementTree.SubElement(
                    plugins_element, "plugin"
                )
                # Add the necessary child elements to the <plugin> element
                group_id_element = ElementTree.SubElement(
                    plugin_surefire_element, "groupId"
                )
                group_id_element.text = "org.apache.maven.plugins"
                artifact_id_element = ElementTree.SubElement(
                    plugin_surefire_element, "artifactId"
                )
                artifact_id_element.text = "maven-surefire-plugin"
                version_element = ElementTree.SubElement(
                    plugin_surefire_element, "version"
                )
                version_element.text = "3.0.0"
                configuration_element = ElementTree.SubElement(
                    plugin_surefire_element, "configuration"
                )
                if self.runAllTests == False:
                    skip_after_failure_element = ElementTree.SubElement(
                        configuration_element, "skipAfterFailureCount"
                    )
                    # Surefire uses skipAfterFailureCount=1 to stop on the first failure.
                    skip_after_failure_element.text = "1"
                    includes_file_element = ElementTree.SubElement(
                        configuration_element, "includesFile"
                    )

                    includes_file_element.text = self.include_file_add
                report_element = ElementTree.SubElement(
                    configuration_element, "reportsDirectory"
                )
                report_element.text = str(
                    os.path.join(
                        self.project_path, "LittleDarwinResults", "test-reports"
                    )
                )
            # Create a new <plugin> element for the Clover plugin
            plugin_clover_element = ElementTree.SubElement(
                plugins_element, "plugin")
            # Add the necessary child elements to the <plugin> element
            group_id_element = ElementTree.SubElement(
                plugin_clover_element, "groupId")
            group_id_element.text = "org.openclover"
            artifact_id_element = ElementTree.SubElement(
                plugin_clover_element, "artifactId"
            )
            artifact_id_element.text = "clover-maven-plugin"
            version_element = ElementTree.SubElement(
                plugin_clover_element, "version")
            version_element.text = "4.5.2"

            clover_configuration_element = ElementTree.SubElement(
                plugin_clover_element, "configuration"
            )
            generate_pdf_element = ElementTree.SubElement(
                clover_configuration_element, "generatePdf"
            )
            generate_pdf_element.text = "false"
            generateXmlElement = ElementTree.SubElement(
                clover_configuration_element, "generateXml"
            )
            generateXmlElement.text = "false"
            generateHtmlElement = ElementTree.SubElement(
                clover_configuration_element, "generateHtml"
            )
            generateHtmlElement.text = "false"
            generateJsonElement = ElementTree.SubElement(
                clover_configuration_element, "generateJson"
            )
            generateJsonElement.text = "false"

            # ? I don't know why this is necessary, but after adding the clover plugin, the build fails unless this is added
            if no_compiler:
                # Create a new <plugin> element for the maven compiler
                plugin_maven_element = ElementTree.SubElement(
                    plugins_element, "plugin")
                # Add the necessary child elements to the <plugin> element
                group_id_element = ElementTree.SubElement(
                    plugin_maven_element, "groupId"
                )
                group_id_element.text = "org.apache.maven.plugins"
                artifact_id_element = ElementTree.SubElement(
                    plugin_maven_element, "artifactId"
                )
                artifact_id_element.text = "maven-compiler-plugin"
                version_element = ElementTree.SubElement(
                    plugin_maven_element, "version"
                )
                version_element.text = "3.8.1"
                configuration_element = ElementTree.SubElement(
                    plugin_maven_element, "configuration"
                )
                source_element = ElementTree.SubElement(
                    configuration_element, "source")
                source_element.text = "1.8"
                target_element = ElementTree.SubElement(
                    configuration_element, "target")
                target_element.text = "1.8"

        Path(self.include_file_add).touch()
        # Save the modified pom.xml file
        tree.write(self.build_file_path)

    def __init__(
        self,
        project_path,
        clover_db_extractor_path,
        build_file_path,
        build_type,
        sqlDB_path,
        D_args=[],
        runAllTests=False,
        timeout=60,
        source_path=None,
    ) -> None:
        """Initialize coverage runner with project/build configuration."""
        self.runAllTests = runAllTests
        self.project_path = project_path
        self.clover_db_extractor_path = str(clover_db_extractor_path)
        self.timeout = timeout
        # build_type is the executable token/path (e.g., "mvn", "C:\\...\\mvn.cmd", "gradlew.bat")
        self.build_type = build_type
        self.build_kind = detect_build_tool(build_type)
        self.build_file_path = build_file_path
        self.D_args = D_args
        self.sqlDB_path = sqlDB_path
        self.source_path = source_path
        # If the build type is maven, and the build file path is not specified, set it to the default
        if self.build_kind == "mvn" and self.build_file_path is None:
            self.build_file_path = str(
                os.path.join(self.project_path, "pom.xml"))
        # If the build type is ant, and the build file path is not specified, set it to the default
        elif self.build_kind == "ant" and self.build_file_path is None:
            self.build_file_path = str(
                os.path.join(self.project_path, "build.xml"))
        # If the build type is gradle, and the build file path is not specified, set it to the default
        elif self.build_kind == "gradle" and self.build_file_path is None:
            # Prefer Groovy DSL if present, otherwise Kotlin DSL, otherwise default to build.gradle
            groovy = os.path.join(self.project_path, "build.gradle")
            kotlin = os.path.join(self.project_path, "build.gradle.kts")
            self.build_file_path = str(groovy if os.path.isfile(
                groovy) else (kotlin if os.path.isfile(kotlin) else groovy))
        # the path to the coverage.xml file

    def search_coverage_XML(self, file_name, line_number):
        """Find tests covering the given file/line in extracted Clover data."""
        file_name = os.path.realpath(file_name)
        if self.tree_clover == None:
            self.__read_coverage_XML()
        test_names = []
        test_names_1 = []
        found = False
        for file in self.tree_clover:
            if os.path.realpath(file["path"]) == file_name:
                for line in file["lines"]:
                    if line["number"] == str(line_number):
                        found = True
                        test_names = line["tests"]
                        break
                    elif line["number"] == "-1":
                        test_names_1 = line["tests"]
                if found == True:
                    break
        if found == False:
            return test_names_1
        return test_names

    def search_line_numbers(
        self, filename, regex=r"line number in original file:\s?(\d+)\s?"
    ):
        """Extract original line numbers from the mutation report text file."""
        with open(filename, "r") as file:
            text = file.read()
        line_numbers = []
        matches = re.findall(regex, text)
        for match in matches:
            line_numbers.append(int(match))
        return line_numbers

    def restore_the_build_file(self):
        """Restore the original build file from the .bak backup."""
        shutil.move(self.build_file_path + ".bak", self.build_file_path)

    def __del__(self):
        """Cleanup large in-memory state on destruction."""
        # ! I moved restoring the original file to another function because of parallel run (I have to test this modification later)
        if self.tree_clover != None:
            del self.tree_clover

    def run_clover(self, test_target, junit_target):
        """Run build with Clover instrumentation and extract DB to SQLite."""
        if self.build_kind == "mvn":
            self._prepare_pom()
            #! **************
            self.clover_db_path = str(
                os.path.join(self.project_path,
                             "LittleDarwinResults", "clover.db")
            )
            self.clover_tmp_db_path = str(
                os.path.join(
                    self.project_path, "LittleDarwinResults", "tmp", "clover.db"
                )
            )
            commandString = [self.build_type, "-f",
                             self.build_file_path, "clean"]
            commandString.extend(self.D_args)
            commandString += [
                "org.openclover:clover-maven-plugin:setup",
                test_target,
                "org.openclover:clover-maven-plugin:clover",
                "-Dmaven.clover.singleCloverDatabase=true",
                "-Dmaven.clover.cloverDatabase=" + self.clover_tmp_db_path,
            ]

            processKilled, processExitCode, runOutput, time_delta = timeoutAlternative(
                commandString,
                workingDirectory=self.project_path,
                timeout=int(self.timeout),
            )

            if processKilled or processExitCode:
                raise subprocess.CalledProcessError(
                    1 if processKilled else processExitCode,
                    commandString,
                    runOutput,
                )

            commandString = [
                self.build_type,
                "-f",
                self.build_file_path,
            ]
            commandString.extend(self.D_args)
            commandString += [
                "org.openclover:clover-maven-plugin:merge",
                "-Dmaven.clover.cloverMergeDatabase=" + self.clover_db_path,
                "-Dmaven.clover.merge.basedir="
                + str(os.path.join(self.project_path,
                      "LittleDarwinResults", "tmp")),
                "clover:clean",
            ]
            processKilled, processExitCode, runOutput, time_delta = timeoutAlternative(
                commandString,
                workingDirectory=self.project_path,
                timeout=int(self.timeout),
            )

            if processKilled or processExitCode:
                raise subprocess.CalledProcessError(
                    1 if processKilled else processExitCode,
                    commandString,
                    runOutput,
                )

            # I moved restoring the pom.xml to the destuctor because some of the plugins were necessary to exclude tests
            # the path to the clover.db file
            commandString = [
                "java",
                "-jar",
                self.clover_db_extractor_path,
                "-f",
                self.clover_db_path,
                "-output_db",
                self.sqlDB_path,
            ]
            processKilled, processExitCode, runOutput, time_delta = timeoutAlternative(
                commandString,
                workingDirectory=self.project_path,
                timeout=int(self.timeout),
            )
            # For coverage collection we still want to import whatever data we can even if
            # some tests fail (common in mixed-framework projects and when running in CI).
            # If the agent ran, it should have produced coverage JSONs that we can merge/import.
            if processKilled:
                raise subprocess.CalledProcessError(
                    1,
                    commandString,
                    runOutput,
                )
        elif self.build_kind == "ant":
            self._prepare_build_xml(junit_target=junit_target)
            # Run Clover code coverage
            #! **************
            commandString = [
                self.build_type,
                "-lib",
                str(
                    os.path.join(
                        self.project_path, "LittleDarwinResults", "jar", "clover.jar"
                    )
                ),
                "-f",
                self.build_file_path,
                "clean",
                "with.clover.mediumdarwin",
                test_target,
                "clean",
            ]
            commandString.extend(self.D_args)

            processKilled, processExitCode, runOutput, time_delta = timeoutAlternative(
                commandString,
                workingDirectory=self.project_path,
                timeout=int(self.timeout),
            )

            if processKilled or processExitCode:
                raise subprocess.CalledProcessError(
                    1 if processKilled else processExitCode,
                    commandString,
                    runOutput,
                )
            # I moved restoring the pom.xml to the destuctor because some of the plugins were necessary to exclude tests
            # the path to the clover.db file
            self.clover_db_path = str(
                os.path.join(self.project_path,
                             "LittleDarwinResults", "clover.db")
            )

            processKilled, processExitCode, runOutput, time_delta = timeoutAlternative(
                [
                    "java",
                    "-jar",
                    str(self.clover_db_extractor_path),
                    "-f",
                    self.clover_db_path,
                    "-output_db",
                    self.sqlDB_path,
                ],
                workingDirectory=self.project_path,
                timeout=int(self.timeout),
            )
            if processKilled or processExitCode:
                raise subprocess.CalledProcessError(
                    1 if processKilled else processExitCode,
                    commandString,
                    runOutput,
                )
        elif self.build_kind == "gradle":
            # Gradle: collect statement coverage via JavaTracerAgent, then import into SQLite.
            agent_jar = self._ensure_java_tracer_agent_jar()
            trace_file = os.path.join(
                self.project_path, "LittleDarwinResults", "trace.json"
            )
            base_coverage_file = os.path.join(
                self.project_path, "LittleDarwinResults", "trace_coverage.json"
            )
            coverage_file = base_coverage_file
            init_script = self._prepare_gradle_java_tracer(
                agent_jar, trace_file, base_coverage_file
            )

            commandString = [
                self.build_type,
                "-I",
                init_script,
                "clean",
                test_target,
            ]
            # Preserve user -D args (e.g., build scan flags). On Windows, quote dotted -D args so Gradle
            # doesn't interpret ".foo=bar" as a task selector.
            for a in (self.D_args or []):
                commandString.append(a)
            processKilled, processExitCode, runOutput, time_delta = timeoutAlternative(
                commandString,
                workingDirectory=self.project_path,
                timeout=int(self.timeout),
            )
            # For coverage collection we still want to import whatever data we can even if
            # some tests fail (common in mixed-framework projects). If the agent ran, it should
            # have produced coverage JSONs that we can merge/import.
            if processKilled:
                raise subprocess.CalledProcessError(
                    1,
                    commandString,
                    runOutput,
                )

            # Merge all per-process coverage files (trace_coverage.<pid>.json) into base file
            self._merge_pid_coverage_files(base_coverage_file)

            # If the expected coverage file isn't present, try a small fallback search under LittleDarwinResults.
            if not os.path.isfile(base_coverage_file):
                lr = os.path.join(self.project_path, "LittleDarwinResults")
                candidates = []
                try:
                    candidates.extend(list(Path(lr).rglob("*coverage*.json")))
                except Exception:
                    pass
                if candidates:
                    newest = max(candidates, key=lambda p: p.stat().st_mtime)
                    coverage_file = str(newest)
                else:
                    coverage_file = base_coverage_file
            else:
                coverage_file = base_coverage_file

            # Import merged coverage file into database
            if os.path.isfile(coverage_file):
                self._import_java_tracer_coverage_to_db(coverage_file)
        else:
            raise ValueError(
                f"Unsupported build tool for coverage: {self.build_type}")
            self._clean_clover_from_build_xml(junit_target=junit_target)
