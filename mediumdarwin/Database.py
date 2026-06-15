"""SQLite-backed persistence layer for mutation data and coverage mapping."""
import sqlite3
import os
import dill
from mediumdarwin.SharedFunctions import getAllInstantiableSubclasses
from mediumdarwin.SharedFunctions import MutationOperator
from mediumdarwin.SharedFunctions import normalize_file_path


class Database:
    NO_TEST = -1
    INSTURMENTED_NOT_COVERED = -2
    NO_INFO = -3

    RES_ID_BUILD_FAILURE = -1
    RES_ID_KILLED_MUTANT = 0
    RES_ID_KILLED_BY_FAILURE_MUTANT = 0
    RES_ID_KILLED_BY_ERROR_MUTANT = 2
    RES_ID_SURVIVED_MUTANT = 1
    RES_ID_NON_COVERED = -2
    RES_ID_TIMEOUT = 3

    def insert_file(self, file_name, project_root=None, options=None):
        """Insert a file into the database, normalizing the path to be relative to buildPath.

        Args:
            file_name: File name (can be absolute or relative)
            project_root: Project root for normalization (deprecated, use options instead)
            options: Options object with buildPath and sourcePath

        Returns:
            File ID. If the file already exists, returns the existing ID instead of creating a duplicate.
        """
        # Determine the buildPath to use for normalization
        build_path = None
        if options and hasattr(options, 'buildPath'):
            build_path = options.buildPath
        elif project_root:
            # For backward compatibility, use project_root as buildPath
            build_path = project_root

        # Normalize file name to be relative to buildPath
        if build_path:
            normalized_name = normalize_file_path(file_name, build_path)
        else:
            # If no buildPath provided, normalize as-is (absolute path with forward slashes)
            normalized_name = normalize_file_path(file_name, None)

        # Check if file already exists
        self.cursor.execute(
            "SELECT id FROM file WHERE name = ?", (normalized_name,))
        existing = self.cursor.fetchone()
        if existing:
            return existing[0]

        # File doesn't exist, insert it
        return self.insert_data("file", "name", [normalized_name])

    def insert_mutation(
        self,
        id,
        file_id,
        node_id,
        startPos,
        endPos,
        lineNo,
        replacementText,
        mutation_operator_id,
        node_json=[],
        new_node_id=[],
        new_node_type=[],
        is_compile_time=0,
        object_=None
    ):
        return self.insert_data(
            "mutation",
            "id, file_id, node_id, startPos, endPos, lineNo, replacementText, mutation_operator_id, new_node_json, new_node_id, new_node_type, compile_time, object",
            [
                id,
                file_id,
                node_id,
                startPos,
                endPos,
                lineNo,
                replacementText,
                mutation_operator_id,
                repr(node_json),
                repr(new_node_id),
                repr(new_node_type),
                str(is_compile_time),
                "NULL" if object_ is None else object_,
            ],
        )

    def insert_mutant(self, mutant_id, mutation_id):
        return self.insert_data("mutant", "id, mutation_id", [mutant_id, mutation_id])

    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.create_table("mutation_operator",
                          "id INTEGER PRIMARY KEY, name TEXT")
        # self.create_trigger_for_mutantion_operator()
        subclasses = getAllInstantiableSubclasses(MutationOperator)
        for subclass in subclasses:
            self.insert_data("mutation_operator", "name", [subclass.__name__])

        self.create_table(
            "mutant",
            "id INTEGER, mutation_id INTEGER, FOREIGN KEY (mutation_id) REFERENCES mutation(id)",
        )
        self.create_table(
            "test_coverage",
            "file_id INTEGER, line_no INTEGER, test_id TEXT",
        )
        self.create_table(
            "test",
            "id INTEGER PRIMARY KEY, qualified_name TEXT",
        )
        self.insert_data("test", "id,qualified_name", [
                         self.INSTURMENTED_NOT_COVERED, "-"])
        self.insert_data("test", "id,qualified_name", [self.NO_TEST, "?"])
        self.insert_data("test", "id,qualified_name", [self.NO_INFO, "*"])

        self.create_table(
            "file",
            "name TEXT, id INTEGER PRIMARY KEY, json TEXT",
        )
        # self.create_trigger_for_file()

        self.create_table(
            "mutation",
            "id INTEGER PRIMARY KEY, file_id INTEGER, startPos INTEGER, endPos INTEGER, lineNo INTEGER, node_id INTEGER, mutation_operator_id INTEGER, replacementText TEXT, new_node_json TEXT, new_node_id TEXT, new_node_type TEXT, compile_time BOOL, object BLOB",
        )
        self.create_table(
            "mutant_test",
            "mutant_id INTEGER, test_id INTEGER, result INTEGER, time TEXT,message TEXT",
        )

    def create_table(self, table_name, columns):
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
        self.cursor.execute(query)

    def insert_data(self, table_name, columns, values):
        value_holder = ",".join(["?"] * len(values))
        query = f"INSERT INTO {table_name} ({columns}) VALUES({value_holder})"
        try:
            self.cursor.execute(query, (values))
            self.conn.commit()
        except Exception as e:
            print(str(e) + " in " + query)
            return False
        if self.cursor.rowcount > 0:
            return self.cursor.lastrowid
        else:
            return False

    def insert_many(self, table_name, columns, values):
        if len(values) == 0:
            return
        value_holder = ",".join(["?"] * len(values[0]))
        query = f"INSERT INTO {table_name} ({columns}) VALUES({value_holder})"
        try:
            self.cursor.executemany(query, values)
            self.conn.commit()
        except Exception as e:
            print(e)
            return False
        if self.cursor.rowcount > 0:
            return self.cursor.lastrowid
        else:
            return False

    def construct_compile_mutations(self, options=None):
        compile_mutations = []
        query = "SELECT name as file_name, object from mutation JOIN mutant on mutant.mutation_id=mutation.id JOIN file on mutation.file_id=file.id WHERE mutation.compile_time=1"
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        for res in results:
            compile_mutations.append((res[0], dill.loads(res[1])))

        # Convert file paths from buildPath-relative (as stored in DB) to sourcePath-relative
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            normalized_results = []
            for res in compile_mutations:
                res = list(res)  # convert tuple to list
                # Convert relative path from DB (buildPath-relative) to absolute, then to relative from sourcePath
                res[0] = os.path.abspath(
                    os.path.join(options.buildPath, res[0]))
                res[0] = os.path.relpath(res[0], options.sourcePath)
                # Normalize path separators to forward slashes for consistency
                res[0] = res[0].replace("\\", "/")
                normalized_results.append(tuple(res))
            return normalized_results

        return compile_mutations

    def construct_mutant_dict(self, options):
        query = "SELECT file.name as file_name, mutant.id as mutant_id, mutation.id as mutation_id, GROUP_CONCAT(mutation.id, ', ') as mutation_list FROM mutation JOIN mutant on mutant.mutation_id=mutation.id JOIN file on mutation.file_id=file.id GROUP BY mutant.id"
        self.cursor.execute(query)
        results = self.cursor.fetchall()

        mutants_dict = dict()
        for res in results:
            res = list(res)  # convert the tuple to a list
            # first convert the relative path to an absolute path using options.buildPath then convert the path to a relative path from the source path
            res[0] = os.path.abspath(os.path.join(options.buildPath, res[0]))
            res[0] = os.path.relpath(res[0], options.sourcePath)
            # Normalize path separators to forward slashes for consistency
            res[0] = res[0].replace("\\", "/")
            if res[0] not in mutants_dict.keys():
                mutants_dict[res[0]] = dict()
            mutants_dict[res[0]][res[1]] = {
                int(x.strip()) for x in res[3].split(",") if x.strip()
            }

        return mutants_dict

    def fetch_build_failure_mutants(self, options=None):
        """Fetch build failure mutants. Convert file paths from buildPath-relative to sourcePath-relative in results.

        Args:
            options: Options object with buildPath and sourcePath

        Returns:
            List of tuples (file_name, mutant_id) where file_name is relative to sourcePath
        """
        query = "SELECT file.name as name, mutant.id as mutant_id FROM mutant_test JOIN mutant ON mutant.id = mutant_test.mutant_id JOIN mutation ON mutation.id = mutant.mutation_id JOIN file ON mutation.file_id = file.id WHERE result = -1"
        self.cursor.execute(query)
        results = self.cursor.fetchall()

        # Convert file paths from buildPath-relative (as stored in DB) to sourcePath-relative
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            normalized_results = []
            for res in results:
                res = list(res)  # convert tuple to list
                # Convert relative path from DB (buildPath-relative) to absolute, then to relative from sourcePath
                res[0] = os.path.abspath(
                    os.path.join(options.buildPath, res[0]))
                res[0] = os.path.relpath(res[0], options.sourcePath)
                # Normalize path separators to forward slashes for consistency
                res[0] = res[0].replace("\\", "/")
                normalized_results.append(tuple(res))
            return normalized_results

        return results

    def fetch_data(self, table_name, columns="*", condition=None):
        query = f"SELECT {columns} FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def fetch_coverage(self, file_name, line_no, options=None):
        """Fetch coverage for a file. Convert file_name from sourcePath-relative to buildPath-relative before querying.

        Args:
            file_name: File name (relative to sourcePath)
            line_no: Line numbers as string (e.g., "1,2,3") or list of integers
            options: Options object with buildPath and sourcePath
        """
        # Convert file_name from sourcePath-relative to buildPath-relative for database query
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            # Convert sourcePath-relative to absolute, then to buildPath-relative
            file_name_abs = os.path.abspath(
                os.path.join(options.sourcePath, file_name))
            file_name_build_relative = os.path.relpath(
                file_name_abs, options.buildPath)
            # Normalize path separators to forward slashes for consistency
            file_name = file_name_build_relative.replace("\\", "/")

        # Handle line_no: can be string like "1,2,3" or list of integers
        if isinstance(line_no, list):
            # Convert list to comma-separated string, validating all are integers
            line_no_str = ",".join(str(int(x)) for x in line_no)
        elif isinstance(line_no, str):
            # Validate string contains only digits, commas, and spaces
            import re
            if not re.match(r'^[\d,\s]+$', line_no):
                raise ValueError(f"Invalid line_no format: {line_no}")
            # Clean up: remove spaces and ensure proper format
            line_no_str = ",".join(str(int(x.strip()))
                                   for x in line_no.split(",") if x.strip())
        else:
            # Single integer
            line_no_str = str(int(line_no))

        query = f"SELECT test.qualified_name from test_coverage JOIN file on file.id=test_coverage.file_id JOIN test on test.id=test_coverage.test_id WHERE file.name=? AND test_coverage.line_no IN ({line_no_str})"
        self.cursor.execute(query, (file_name,))
        file_coverage = self.cursor.fetchall()
        return file_coverage

    def fetch_all_coverage(self):
        query = f"SELECT test.qualified_name from test where test.id!=-2"
        self.cursor.execute(query)
        file_coverage = self.cursor.fetchall()
        return file_coverage

    def fetch_mutated_files_count(self):
        query = "SELECT DISTINCT SUM(COUNT(DISTINCT mutant.id)) OVER() AS total_count FROM file JOIN mutation on mutation.file_id=file.id join mutant on mutant.mutation_id=mutation.id GROUP BY file.name ORDER BY file.name"
        self.cursor.execute(query)
        return int(self.cursor.fetchall()[0][0])

    def fetch_mutated_files(self, options=None):
        """Fetch mutated files. Convert file paths from buildPath-relative to sourcePath-relative in results.

        Args:
            options: Options object with buildPath and sourcePath

        Returns:
            List of tuples (file_name, total_count) where file_name is relative to sourcePath
        """
        query = "SELECT DISTINCT file.name as name, COUNT(DISTINCT mutant.id) AS total_count FROM file JOIN mutation on mutation.file_id=file.id join mutant on mutant.mutation_id=mutation.id GROUP BY file.name ORDER BY file.name"
        self.cursor.execute(query)
        results = self.cursor.fetchall()

        # Convert file paths from buildPath-relative (as stored in DB) to sourcePath-relative
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            normalized_results = []
            for res in results:
                res = list(res)  # convert tuple to list
                # Convert relative path from DB (buildPath-relative) to absolute, then to relative from sourcePath
                res[0] = os.path.abspath(
                    os.path.join(options.buildPath, res[0]))
                res[0] = os.path.relpath(res[0], options.sourcePath)
                # Normalize path separators to forward slashes for consistency
                res[0] = res[0].replace("\\", "/")
                normalized_results.append(tuple(res))
            return normalized_results

        return results

    def fetch_mutations(self):
        query = "SELECT * FROM mutation"
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return results

    def fetch_last_mutant_ID(self):
        query = "SELECT max(id) FROM mutant"
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        if res:
            res = res[0][0]
        else:
            res = 0
        return res

    def fetch_mutants(self, options=None):
        """Fetch all mutants. Convert file paths from buildPath-relative to sourcePath-relative in results.

        Args:
            options: Options object with buildPath and sourcePath

        Returns:
            List of tuples (file_name, mutant_id, lineNo) where file_name is relative to sourcePath
        """
        query = 'SELECT file.name as name, mutant.id as id, group_concat(mutation.lineNo , ",") as lineNo FROM file JOIN mutation ON file.id = mutation.file_id JOIN mutant ON mutant.mutation_id = mutation.id GROUP BY mutant.id ORDER BY file.name'
        self.cursor.execute(query)
        results = self.cursor.fetchall()

        # Convert file paths from buildPath-relative (as stored in DB) to sourcePath-relative
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            normalized_results = []
            for res in results:
                res = list(res)  # convert tuple to list
                # Convert relative path from DB (buildPath-relative) to absolute, then to relative from sourcePath
                res[0] = os.path.abspath(
                    os.path.join(options.buildPath, res[0]))
                res[0] = os.path.relpath(res[0], options.sourcePath)
                # Normalize path separators to forward slashes for consistency
                res[0] = res[0].replace("\\", "/")
                normalized_results.append(tuple(res))
            return normalized_results

        return results

    def fetch_file_mutant_by_mutation_ID(self, mutation_id, options=None):
        """Fetch file mutants by mutation ID. Convert file paths from buildPath-relative to sourcePath-relative in results.

        Args:
            mutation_id: Mutation ID to search for
            options: Options object with buildPath and sourcePath

        Returns:
            List of tuples (file_name, mutant_id, lineNo) where file_name is relative to sourcePath
        """
        query = f"SELECT file.name as name, mutant.id as id, group_concat(mutation.lineNo , ',') as lineNo FROM file JOIN mutation ON file.id = mutation.file_id JOIN mutant ON mutant.mutation_id = mutation.id WHERE mutation_id = ? GROUP BY mutant.id ORDER BY file.name"
        self.cursor.execute(query, (mutation_id,))
        results = self.cursor.fetchall()

        # Convert file paths from buildPath-relative (as stored in DB) to sourcePath-relative
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            normalized_results = []
            for res in results:
                res = list(res)  # convert tuple to list
                # Convert relative path from DB (buildPath-relative) to absolute, then to relative from sourcePath
                res[0] = os.path.abspath(
                    os.path.join(options.buildPath, res[0]))
                res[0] = os.path.relpath(res[0], options.sourcePath)
                # Normalize path separators to forward slashes for consistency
                res[0] = res[0].replace("\\", "/")
                normalized_results.append(tuple(res))
            return normalized_results

        return results

    def fetch_file_mutant(self, file_name, options=None):
        """Fetch file mutants. Convert file_name from sourcePath-relative to buildPath-relative before querying, normalize results if options provided."""
        # Convert file_name from sourcePath-relative to buildPath-relative for database query
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            # Convert sourcePath-relative to absolute, then to buildPath-relative
            file_name_abs = os.path.abspath(
                os.path.join(options.sourcePath, file_name))
            file_name_build_relative = os.path.relpath(
                file_name_abs, options.buildPath)
            # Normalize path separators to forward slashes for consistency
            file_name = file_name_build_relative.replace("\\", "/")

        query = f"SELECT file.name as name, mutant.id as id, group_concat(mutation.lineNo , ',') as lineNo FROM file JOIN mutation ON file.id = mutation.file_id JOIN mutant ON mutant.mutation_id = mutation.id WHERE file.name = ? GROUP BY mutant.id ORDER BY file.name"
        self.cursor.execute(query, (file_name,))
        sqlLiteDB_File_Mutant = self.cursor.fetchall()

        # Normalize file paths in results if options provided
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            normalized_results = []
            for res in sqlLiteDB_File_Mutant:
                res = list(res)  # convert tuple to list
                # Convert relative path from DB to absolute using buildPath, then to relative from sourcePath
                res[0] = os.path.abspath(
                    os.path.join(options.buildPath, res[0]))
                res[0] = os.path.relpath(res[0], options.sourcePath)
                # Normalize path separators to forward slashes for consistency
                res[0] = res[0].replace("\\", "/")
                normalized_results.append(tuple(res))
            return normalized_results

        return sqlLiteDB_File_Mutant

    def fetch_file_mutant_with_id(self, file_name, mutant_id, options=None):
        """Fetch file mutants with specific ID. Convert file_name from sourcePath-relative to buildPath-relative before querying, normalize results if options provided."""
        # Convert file_name from sourcePath-relative to buildPath-relative for database query
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            # Convert sourcePath-relative to absolute, then to buildPath-relative
            file_name_abs = os.path.abspath(
                os.path.join(options.sourcePath, file_name))
            file_name_build_relative = os.path.relpath(
                file_name_abs, options.buildPath)
            # Normalize path separators to forward slashes for consistency
            file_name = file_name_build_relative.replace("\\", "/")

        query = f"SELECT file.name as name, mutant.id as id, group_concat(mutation.lineNo , ',') as lineNo FROM file JOIN mutation ON file.id = mutation.file_id JOIN mutant ON mutant.mutation_id = mutation.id WHERE file.name = ? and mutant.id = ? GROUP BY mutant.id ORDER BY file.name"
        self.cursor.execute(query, (file_name, mutant_id))
        sqlLiteDB_File_Mutant = self.cursor.fetchall()

        # Normalize file paths in results if options provided
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            normalized_results = []
            for res in sqlLiteDB_File_Mutant:
                res = list(res)  # convert tuple to list
                # Convert relative path from DB to absolute using buildPath, then to relative from sourcePath
                res[0] = os.path.abspath(
                    os.path.join(options.buildPath, res[0]))
                res[0] = os.path.relpath(res[0], options.sourcePath)
                # Normalize path separators to forward slashes for consistency
                res[0] = res[0].replace("\\", "/")
                normalized_results.append(tuple(res))
            return normalized_results

        return sqlLiteDB_File_Mutant

    def update_file_json(self, file_name, json, options=None):
        """Update file JSON. Convert file_name from sourcePath-relative to buildPath-relative before querying."""
        # Convert file_name from sourcePath-relative to buildPath-relative for database query
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            # Convert sourcePath-relative to absolute, then to buildPath-relative
            file_name_abs = os.path.abspath(
                os.path.join(options.sourcePath, file_name))
            file_name_build_relative = os.path.relpath(
                file_name_abs, options.buildPath)
            # Normalize path separators to forward slashes for consistency
            file_name = file_name_build_relative.replace("\\", "/")

        query = f"UPDATE file SET json = ? WHERE name = ?"
        self.cursor.execute(query, (json, file_name))
        self.conn.commit()

        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def update_data(self, table_name, set_values, condition=None):
        query = f"UPDATE {table_name} SET {set_values}"
        if condition:
            query += f" WHERE {condition}"
        try:
            self.cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            print(e)
            return False
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def delete_data(self, table_name, condition=None):
        query = f"DELETE FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        try:
            self.cursor.execute(query)
            self.conn.commit()
        except Exception:
            return False

        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def ensure_test_placeholders(self):
        """Ensure special placeholder tests exist in the database."""
        self.cursor.execute(
            "INSERT OR IGNORE INTO test (id, qualified_name) VALUES (?, ?)",
            (self.INSTURMENTED_NOT_COVERED, "-"),
        )
        self.cursor.execute(
            "INSERT OR IGNORE INTO test (id, qualified_name) VALUES (?, ?)",
            (self.NO_TEST, "?"),
        )
        self.cursor.execute(
            "INSERT OR IGNORE INTO test (id, qualified_name) VALUES (?, ?)",
            (self.NO_INFO, "*"),
        )
        self.conn.commit()

    def clear_test_coverage(self):
        """Clear all test coverage entries."""
        self.cursor.execute("DELETE FROM test_coverage")
        self.conn.commit()

    def get_all_tests_dict(self):
        """Get all tests as a dictionary mapping qualified_name to id."""
        self.cursor.execute("SELECT id, qualified_name FROM test")
        return {row[1]: row[0] for row in self.cursor.fetchall() if row[1] is not None}

    def get_or_create_test_id(self, qualified_name):
        """Get or create a test by qualified_name and return its ID.

        Args:
            qualified_name: Test qualified name

        Returns:
            Test ID. Returns NO_INFO if name is None or "unknown".
        """
        if not qualified_name or qualified_name.strip().lower() == "unknown":
            return self.NO_INFO

        # Check if test exists
        self.cursor.execute(
            "SELECT id FROM test WHERE qualified_name = ?", (qualified_name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]

        # Create new test
        self.cursor.execute(
            "INSERT INTO test (qualified_name) VALUES (?)", (qualified_name,))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_file_id_with_fallback(self, file_name, options=None):
        """Get file ID with fallback logic for handling duplicate file entries.

        This method tries to find a file by exact name first, then
        by basename matching to handle cases where the same file was stored
        with different path formats.

        Args:
            file_name: File name (relative to sourcePath if options provided, otherwise used as-is)
            options: Options object with buildPath and sourcePath

        Returns:
            File ID. Creates a new file entry if not found.
        """
        # Convert file_name from sourcePath-relative to buildPath-relative for database query
        original_file_name = file_name
        if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
            # Convert sourcePath-relative to absolute, then to buildPath-relative
            file_name_abs = os.path.abspath(
                os.path.join(options.sourcePath, file_name))
            file_name_build_relative = os.path.relpath(
                file_name_abs, options.buildPath)
            # Normalize path separators to forward slashes for consistency
            file_name = file_name_build_relative.replace("\\", "/")

        # Try exact match first
        self.cursor.execute(
            "SELECT id FROM file WHERE name = ?", (file_name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]

        # Try to find files with the same basename to handle duplicates
        # Since file names in the database use forward slashes, use forward slash for basename extraction
        # Use the converted file_name for basename extraction
        file_name_parts = file_name.split('/')
        base = file_name_parts[-1] if file_name_parts else os.path.basename(
            file_name)

        if base and base != file_name:
            # Find files that end with the same basename
            # Database stores paths with forward slashes, so only use forward slash pattern
            self.cursor.execute(
                "SELECT id, name FROM file WHERE name = ? OR name LIKE ?",
                (base, f"%/{base}"))
            rows = self.cursor.fetchall()
            if rows:
                # Filter to only exact basename matches to avoid false positives
                matching_rows = []
                for r in rows:
                    existing_name = r[1] or ""
                    # Extract basename using forward slash since database uses forward slashes
                    existing_parts = existing_name.split('/')
                    existing_base = existing_parts[-1] if existing_parts else existing_name
                    # Only match if basenames are exactly the same
                    if existing_base == base:
                        matching_rows.append(r)

                if matching_rows:
                    # Prefer the most complete path (longest) that matches
                    matching_rows.sort(key=lambda r: (
                        0 if (r[1] == file_name) else 1,
                        -len(r[1] or ""),
                        0 if (r[1] or "").startswith("src/") else 1
                    ))
                    # Return the best match
                    return matching_rows[0][0]

        # Create new file row with converted file_name (buildPath-relative)
        self.cursor.execute(
            "INSERT INTO file (name) VALUES (?)", (file_name,))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_mutated_lines(self, options=None):
        """Get all mutated lines from the mutation table. Convert file paths from buildPath-relative to sourcePath-relative in results.

        Args:
            options: Options object with buildPath and sourcePath

        Returns:
            List of tuples (file_name, line_no) where file_name is relative to sourcePath
        """
        try:
            self.cursor.execute(
                "SELECT DISTINCT file.name, mutation.lineNo "
                "FROM mutation JOIN file ON file.id = mutation.file_id "
                "WHERE mutation.lineNo IS NOT NULL"
            )
            results = self.cursor.fetchall()

            # Convert file paths from buildPath-relative (as stored in DB) to sourcePath-relative
            if options and hasattr(options, 'buildPath') and hasattr(options, 'sourcePath'):
                normalized_results = []
                for res in results:
                    res = list(res)  # convert tuple to list
                    # Convert relative path from DB (buildPath-relative) to absolute, then to relative from sourcePath
                    res[0] = os.path.abspath(
                        os.path.join(options.buildPath, res[0]))
                    res[0] = os.path.relpath(res[0], options.sourcePath)
                    # Normalize path separators to forward slashes for consistency
                    res[0] = res[0].replace("\\", "/")
                    normalized_results.append(tuple(res))
                return normalized_results

            return results
        except Exception:
            return []

    def get_existing_test_coverage(self):
        """Get all existing test_coverage entries as a set of (file_id, line_no) tuples.

        Returns:
            Set of (file_id, line_no) tuples.
        """
        self.cursor.execute("SELECT file_id, line_no FROM test_coverage")
        existing = set()
        for fid, ln in self.cursor.fetchall():
            try:
                existing.add((int(fid), int(ln)))
            except Exception:
                pass
        return existing

    def get_mutated_lines_by_file_id(self):
        """Get all mutated lines directly by file_id, bypassing path normalization issues.

        This method queries the database directly for (file_id, line_no) pairs that have mutations,
        which is useful for backfilling coverage for files that are in the database but not in
        trace_coverage.json.

        Returns:
            Set of (file_id, line_no) tuples where file_id is the database file ID.
        """
        try:
            self.cursor.execute(
                "SELECT DISTINCT mutation.file_id, mutation.lineNo "
                "FROM mutation "
                "WHERE mutation.lineNo IS NOT NULL AND mutation.lineNo > 0"
            )
            results = set()
            for file_id, line_no in self.cursor.fetchall():
                try:
                    file_id_int = int(file_id)
                    line_no_int = int(line_no)
                    if line_no_int > 0:
                        results.add((file_id_int, line_no_int))
                except Exception:
                    pass
            return results
        except Exception:
            return set()

    def verify_mutation_coverage_completeness(self):
        """Verify that all mutations have corresponding test_coverage entries.

        This method checks if there are any (file_id, line_no) pairs in the mutation table
        that don't have corresponding entries in the test_coverage table.

        Returns:
            Set of (file_id, line_no) tuples that are missing from test_coverage.
        """
        try:
            # Get all mutated lines
            mutated_lines = self.get_mutated_lines_by_file_id()

            # Get all existing coverage entries
            existing_coverage = self.get_existing_test_coverage()

            # Find missing entries
            missing = mutated_lines - existing_coverage
            return missing
        except Exception:
            return set()

    def insert_test_coverage_bulk(self, coverage_entries):
        """Bulk insert test coverage entries.

        Args:
            coverage_entries: List of tuples (file_id, line_no, test_id)
        """
        if not coverage_entries:
            return
        self.cursor.executemany(
            "INSERT INTO test_coverage (file_id, line_no, test_id) VALUES (?, ?, ?)",
            coverage_entries,
        )
        self.conn.commit()

    def close_connection(self):
        self.conn.close()
