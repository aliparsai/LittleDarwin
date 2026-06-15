import os
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as ET

database_stub = types.ModuleType("mediumdarwin.Database")
database_stub.Database = object
sys.modules.setdefault("mediumdarwin.Database", database_stub)

shared_functions_stub = types.ModuleType("mediumdarwin.SharedFunctions")
shared_functions_stub.timeoutAlternative = lambda *args, **kwargs: None
shared_functions_stub.detect_build_tool = lambda build_type: "mvn"
shared_functions_stub.normalize_file_path = lambda path: path
sys.modules.setdefault("mediumdarwin.SharedFunctions", shared_functions_stub)

from mediumdarwin.LineCoverage import LineCoverage


POM_TEMPLATE = """<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId>
  <artifactId>demo</artifactId>
  <version>1.0-SNAPSHOT</version>
  {extra}
</project>
"""


class TestLineCoverageMavenSurefire(unittest.TestCase):
    def _make_line_coverage(self, tmpdir, pom_path):
        return LineCoverage(
            project_path=tmpdir,
            clover_db_extractor_path=os.path.join(tmpdir, "dummy-extractor.jar"),
            build_file_path=pom_path,
            build_type="mvn",
            sqlDB_path=os.path.join(tmpdir, "mutationdatabase.db"),
            D_args=[],
            runAllTests=False,
            timeout=1,
        )

    def _parse_xml(self, pom_path):
        tree = ET.parse(pom_path)
        root = tree.getroot()
        namespace = {"m": root.tag.split("}")[0].strip("{")}
        return root, namespace

    def test_add_tests_to_pom_xml_sets_skip_after_first_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pom_path = os.path.join(tmpdir, "pom.xml")
            include_path = os.path.join(tmpdir, "include-tests.txt")
            report_path = os.path.join(tmpdir, "reports")
            pom_xml = POM_TEMPLATE.format(
                extra="""
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
"""
            )
            with open(pom_path, "w", encoding="utf-8") as f:
                f.write(pom_xml)

            lc = self._make_line_coverage(tmpdir, pom_path)
            lc.include_file_add = include_path
            lc.add_tests_to_pom_xml(
                include_tests_file=include_path,
                report_path=report_path,
                covered_tests=[("pkg.SampleTest#testMethod",)],
            )

            root, ns = self._parse_xml(pom_path)
            config = root.find(
                ".//m:plugin[m:artifactId='maven-surefire-plugin']/m:configuration",
                ns,
            )
            self.assertIsNotNone(config)
            self.assertEqual(
                config.findtext("m:skipAfterFailureCount", namespaces=ns), "1"
            )
            self.assertEqual(config.findtext("m:includesFile", namespaces=ns), include_path)
            self.assertEqual(
                config.findtext("m:reportsDirectory", namespaces=ns), report_path
            )
            self.assertIsNone(config.find("m:failFast", ns))

    def test_prepare_pom_adds_surefire_plugin_with_skip_after_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pom_path = os.path.join(tmpdir, "pom.xml")
            include_path = os.path.join(tmpdir, "include-tests.txt")
            with open(
                pom_path,
                "w",
                encoding="utf-8",
            ) as f:
                f.write(POM_TEMPLATE.format(extra=""))

            lc = self._make_line_coverage(tmpdir, pom_path)
            lc._prepare_pom(include_path)

            root, ns = self._parse_xml(pom_path)
            surefire_plugin = root.find(
                ".//m:plugin[m:artifactId='maven-surefire-plugin']",
                ns,
            )
            self.assertIsNotNone(surefire_plugin)
            config = surefire_plugin.find("m:configuration", ns)
            self.assertIsNotNone(config)
            self.assertEqual(
                config.findtext("m:skipAfterFailureCount", namespaces=ns), "1"
            )
            self.assertEqual(config.findtext("m:includesFile", namespaces=ns), include_path)
            self.assertIsNone(config.find("m:failFast", ns))


if __name__ == "__main__":
    unittest.main()
