import os
import sys
import unittest

from mediumdarwin.SharedFunctions import (
    detect_build_tool,
    return_build_file,
    change_build_file,
    add_gradle_test_filters,
    write_selected_tests_file,
    add_gradle_test_selection_via_file,
    add_gradle_isolation,
)


class TestGradleHelpers(unittest.TestCase):
    def test_detect_build_tool_handles_windows_paths(self):
        if sys.platform == "win32":
            self.assertEqual(detect_build_tool(
                r"C:\apache-maven\bin\mvn.cmd"), "mvn")
            self.assertEqual(detect_build_tool(r"C:\proj\mvnw.cmd"), "mvn")
            self.assertEqual(detect_build_tool(
                r"C:\apache-ant\bin\ant.bat"), "ant")
            self.assertEqual(detect_build_tool(r"D:\proj\gradlew.bat"), "gradle")
        else:
            # POSIX: test with forward-slash paths that reflect real Linux layouts
            self.assertEqual(detect_build_tool("/usr/bin/mvn"), "mvn")
            self.assertEqual(detect_build_tool("/opt/maven/bin/mvn"), "mvn")
            self.assertEqual(detect_build_tool("./mvnw"), "mvn")
            self.assertEqual(detect_build_tool("/usr/bin/ant"), "ant")
            self.assertEqual(detect_build_tool("./gradlew"), "gradle")
        self.assertEqual(detect_build_tool("gradle"), "gradle")

    def test_return_build_file_does_not_parse_gradle_build_flag(self):
        # Reserved for other plans; should not be treated as build-file selector.
        self.assertIsNone(return_build_file("gradle test -b build.gradle"))
        self.assertIsNone(return_build_file(
            "gradlew test --build-file build.gradle.kts"))

    def test_change_build_file_does_not_inject_gradle_build_flag(self):
        cmd = ["gradlew.bat", "test"]
        out = change_build_file(cmd, r"C:\proj\build.gradle")
        self.assertEqual(out, cmd)

    def test_add_gradle_test_filters_normalizes_hash_separator(self):
        cmd = ["gradle", "test"]
        tests = [("a.b.MyTest#testA",), ("a.b.OtherTest.testB",),
                 ("a.b.MyTest#testA",)]
        out = add_gradle_test_filters(cmd, tests)
        # Hash gets normalized to dot
        joined = " ".join(out)
        self.assertIn("--tests a.b.MyTest.testA", joined)
        self.assertIn("--tests a.b.OtherTest.testB", joined)

    def test_gradle_file_based_selection_adds_init_script_and_property(self):
        cmd = ["gradle", "test"]
        selected_file = write_selected_tests_file(
            target_file="D:/tmp/md-selected-tests.txt",
            covered_tests=[("a.b.MyTest#testA",), ("a.b.OtherTest.testB",)],
        )
        out = add_gradle_test_selection_via_file(
            cmd, project_path="D:/proj", selected_tests_file=selected_file
        )
        joined = " ".join(out)
        self.assertIn("-I", out)
        self.assertIn("md-test-selection.init.gradle", joined)
        self.assertIn("-Dmd.includeTestsFile=", joined)

    def test_gradle_isolation_adds_run_id_and_reports_dir(self):
        cmd = ["gradle", "test"]
        out = add_gradle_isolation(
            cmd,
            project_path="D:/proj",
            run_id="123",
            reports_dir="D:/proj/LittleDarwinResults/123-test_reports",
        )
        joined = " ".join(out)
        self.assertIn("--no-daemon", out)
        self.assertIn("md-gradle-isolation.init.gradle", joined)
        self.assertIn("-Dmd.runId=123", joined)
        self.assertIn("-Dmd.reportsDir=", joined)


if __name__ == "__main__":
    unittest.main()
