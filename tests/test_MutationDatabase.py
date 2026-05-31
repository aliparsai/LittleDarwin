import os
import sqlite3
import tempfile
import unittest

from littledarwin.MutationDatabase import MutationDatabase


class TestMutationDatabase(unittest.TestCase):

    def setUp(self):
        self.tempDir = tempfile.TemporaryDirectory()
        self.dbPath = os.path.join(self.tempDir.name, "mutationdatabase")

    def tearDown(self):
        self.tempDir.cleanup()

    def test_roundtrip_source_files_and_mutants(self):
        with MutationDatabase(self.dbPath, "n") as db:
            db.add_mutant("com/example/Foo.java", 1, "com/example/Foo.java/1.java")
            db.add_mutant("com/example/Foo.java", 2, "com/example/Foo.java/2.java")
            db.add_mutant("com/example/Bar.java", 1, "com/example/Bar.java/1.java")

        with MutationDatabase(self.dbPath, "r") as db:
            self.assertEqual(sorted(db.source_paths()),
                             ["com/example/Bar.java", "com/example/Foo.java"])
            self.assertEqual(db.mutants_for("com/example/Foo.java"),
                             ["com/example/Foo.java/1.java", "com/example/Foo.java/2.java"])
            self.assertEqual(db.mutant_count_for("com/example/Foo.java"), 2)
            self.assertEqual(db.mutant_count_for("com/example/Bar.java"), 1)
            self.assertEqual(db.mutant_count_for("com/example/Nobody.java"), 0)
            self.assertEqual(db.mutants_for("com/example/Nobody.java"), [])

    def test_mutants_for_is_ordered_by_index(self):
        with MutationDatabase(self.dbPath, "n") as db:
            db.add_mutant("Foo.java", 3, "Foo.java/3.java")
            db.add_mutant("Foo.java", 1, "Foo.java/1.java")
            db.add_mutant("Foo.java", 2, "Foo.java/2.java")
            self.assertEqual(
                db.mutants_for("Foo.java"),
                ["Foo.java/1.java", "Foo.java/2.java", "Foo.java/3.java"])

    def test_record_result_flips_status_and_results_for_partitions(self):
        with MutationDatabase(self.dbPath, "n") as db:
            db.add_mutant("Foo.java", 1, "Foo.java/1.java")
            db.add_mutant("Foo.java", 2, "Foo.java/2.java")
            db.add_mutant("Foo.java", 3, "Foo.java/3.java")

            survived, killed = db.results_for("Foo.java")
            self.assertEqual((survived, killed), ([], []))

            db.record_result("Foo.java/1.java", "survived")
            db.record_result("Foo.java/2.java", "killed")
            db.record_result("Foo.java/3.java", "killed")

            survived, killed = db.results_for("Foo.java")
            self.assertEqual(survived, ["1.java"])
            self.assertEqual(killed, ["2.java", "3.java"])

            db.record_result("Foo.java/1.java", "killed")
            survived, killed = db.results_for("Foo.java")
            self.assertEqual(survived, [])
            self.assertEqual(killed, ["1.java", "2.java", "3.java"])

    def test_record_result_rejects_unknown_status(self):
        with MutationDatabase(self.dbPath, "n") as db:
            db.add_mutant("Foo.java", 1, "Foo.java/1.java")
            with self.assertRaises(ValueError):
                db.record_result("Foo.java/1.java", "pending")
            with self.assertRaises(ValueError):
                db.record_result("Foo.java/1.java", "anything-else")

    def test_record_result_unknown_mutant_raises_keyerror(self):
        with MutationDatabase(self.dbPath, "n") as db:
            with self.assertRaises(KeyError):
                db.record_result("does/not/exist.java/1.java", "killed")

    def test_unique_constraints_block_duplicates(self):
        with MutationDatabase(self.dbPath, "n") as db:
            db.add_mutant("Foo.java", 1, "Foo.java/1.java")
            with self.assertRaises(sqlite3.IntegrityError):
                db.add_mutant("Foo.java", 1, "Foo.java/1.java")
            with self.assertRaises(sqlite3.IntegrityError):
                db.add_mutant("Other.java", 1, "Foo.java/1.java")

    def test_density_and_complexity_roundtrip(self):
        with MutationDatabase(self.dbPath, "n") as db:
            db.record_line_densities("Foo.java", [(5, 2), (10, 1), (15, 3)])
            db.record_method_complexities(
                "Foo.java",
                [("myMethod", 4, 3, 12), ("other", 1, 2, 8)])

            conn = sqlite3.connect(self.dbPath)
            try:
                density_rows = conn.execute(
                    "SELECT line_number, mutant_count FROM mutant_density_per_line "
                    "JOIN source_files ON source_files.id = source_file_id "
                    "WHERE path = 'Foo.java' ORDER BY line_number").fetchall()
                complexity_rows = conn.execute(
                    "SELECT method_name, density, cyclomatic, lines_of_code "
                    "FROM complexity_per_method "
                    "JOIN source_files ON source_files.id = source_file_id "
                    "WHERE path = 'Foo.java' ORDER BY method_name").fetchall()
            finally:
                conn.close()

            self.assertEqual(density_rows, [(5, 2), (10, 1), (15, 3)])
            self.assertEqual(complexity_rows,
                             [("myMethod", 4, 3, 12), ("other", 1, 2, 8)])

    def test_density_record_replaces_previous(self):
        with MutationDatabase(self.dbPath, "n") as db:
            db.record_line_densities("Foo.java", [(1, 1), (2, 2)])
            db.record_line_densities("Foo.java", [(3, 3)])

            conn = sqlite3.connect(self.dbPath)
            try:
                rows = conn.execute(
                    "SELECT line_number, mutant_count FROM mutant_density_per_line "
                    "JOIN source_files ON source_files.id = source_file_id "
                    "WHERE path = 'Foo.java'").fetchall()
            finally:
                conn.close()
            self.assertEqual(rows, [(3, 3)])

    def test_read_only_open_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            MutationDatabase(self.dbPath, "r")

    def test_n_flag_wipes_existing_file(self):
        with MutationDatabase(self.dbPath, "n") as db:
            db.add_mutant("Foo.java", 1, "Foo.java/1.java")
        with MutationDatabase(self.dbPath, "n") as db:
            self.assertEqual(db.source_paths(), [])
            self.assertEqual(db.mutants_for("Foo.java"), [])


if __name__ == '__main__':
    unittest.main()
