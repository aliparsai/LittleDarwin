import unittest


from mediumdarwin.Schemata import Schemata


class TestCompileFailureCaretColumn(unittest.TestCase):
    def test_two_group_regex_derives_column_from_caret(self):
        text = (
            "D:\\workdir\\proj\\src\\main\\java\\com\\acme\\Foo.java:10: error: bad operand types for binary operator '-'\n"
            "    return \"a\" - \"b\";\n"
            "               ^\n"
            "  first type:  java.lang.String\n"
            "  second type: java.lang.String\n"
        )

        # 2 groups: (file, line). Column derived from caret.
        regex = r"^(.+\.java):(\d+):\s*error:.*"
        out = Schemata.find_error_mvn(None, text, regex)

        self.assertEqual(len(out), 1)
        self.assertEqual(
            out[0][0], r"D:\workdir\proj\src\main\java\com\acme\Foo.java")
        self.assertEqual(out[0][1], 10)
        # caret is under the '-' in: '    return "a" - "b";'
        # Column is 1-based
        self.assertEqual(out[0][2], 16)

    def test_three_group_regex_uses_provided_column(self):
        text = (
            r"D:\w\Foo.java:10:15: error: bad operand types\n"
            r"...\n"
        )
        regex = r"^(.+\.java):(\d+):(\d+):\s*error:.*"
        out = Schemata.find_error_mvn(None, text, regex)
        self.assertEqual(out, [[r"D:\w\Foo.java", 10, 15]])


if __name__ == "__main__":
    unittest.main()
