import os
import tempfile
import unittest

from mediumdarwin.LineCoverage import LineCoverage


class TestGradleCloverInit(unittest.TestCase):
    def test_prepare_gradle_java_tracer_writes_init_script(self):
        with tempfile.TemporaryDirectory() as td:
            lc = LineCoverage(
                project_path=td,
                clover_db_extractor_path=os.path.join(
                    td, "dummy-extractor.jar"),
                build_file_path=None,
                build_type="gradle",
                sqlDB_path=os.path.join(td, "mutationdatabase.db"),
                D_args=[],
                runAllTests=False,
                timeout=1,
            )
            init_path = lc._prepare_gradle_java_tracer(
                agent_jar=os.path.join(td, "LittleDarwinResults", "jar", "java-tracer-agent.jar"),
                trace_file=os.path.join(td, "LittleDarwinResults", "trace.json"),
                coverage_file=os.path.join(td, "LittleDarwinResults", "trace_coverage.json"),
            )
            self.assertTrue(os.path.isfile(init_path))
            with open(init_path, encoding="utf-8") as f:
                txt = f.read()
            # V2 of the tracer embeds paths directly as JVM args instead of
            # using -D Gradle properties (avoids Windows CLI parsing quirks).
            self.assertIn("MD_JAVA_TRACER_V2", txt)
            self.assertIn("-javaagent", txt.lower())
            self.assertIn("upToDateWhen", txt)
            self.assertIn("allprojects", txt)


if __name__ == "__main__":
    unittest.main()
