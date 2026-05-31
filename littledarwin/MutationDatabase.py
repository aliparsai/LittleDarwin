import os
import sqlite3


_VALID_STATUSES = ("pending", "survived", "killed")


class MutationDatabase(object):
    """
    Relational SQLite store for a LittleDarwin run.

    Earlier versions used ``shelve`` (cross-platform incompatible) and then a
    pickle-BLOB SQLite store. This version persists the same information in a
    normalized relational schema so anyone — a SQL client, a downstream tool,
    a future LittleDarwin feature — can query it directly without unpickling.

    Schema (five tables, one SQLite file per run):

    * ``source_files(id, path)`` — one row per mutated Java source file.
      ``path`` is the source-relative path (e.g. ``com/example/Foo.java``).
    * ``mutants(id, source_file_id, mutant_index, mutant_path, build_status)``
      — one row per generated mutant file. ``mutant_index`` is the ``N`` in
      ``N.java``; ``mutant_path`` is the relative path under the mutants
      directory; ``build_status`` is one of ``pending`` (after mutation phase),
      ``survived``, or ``killed`` (after build phase).
    * ``mutant_density_per_line(source_file_id, line_number, mutant_count)``
      — same data that's also dumped to ``MutantDensityPerLine.csv``.
    * ``complexity_per_method(source_file_id, method_name, density,
      cyclomatic, lines_of_code)`` — same data as ``ComplexityPerMethod.csv``.

    Mutation databases are regenerated each run; there is no backward
    compatibility with older shelve or pickle-BLOB databases.
    """

    def __init__(self, databasePath, flag="c"):
        """
        Opens (or creates) the database.

        :param databasePath: Path to the SQLite database file.
        :type databasePath: str
        :param flag: Open mode, mirroring ``shelve``/``dbm`` semantics:
                     ``"r"`` read-only (the file must already exist),
                     ``"c"`` open for read/write, creating the file if needed,
                     ``"n"`` always create a new, empty database.
        :type flag: str
        """
        self.databasePath = databasePath

        if flag == "n" and os.path.exists(databasePath):
            os.remove(databasePath)

        if flag == "r" and not os.path.exists(databasePath):
            raise FileNotFoundError("Database does not exist: " + str(databasePath))

        self.connection = sqlite3.connect(databasePath)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._createSchema()

    def _createSchema(self):
        cursor = self.connection.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS source_files (
                id   INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS mutants (
                id             INTEGER PRIMARY KEY,
                source_file_id INTEGER NOT NULL REFERENCES source_files(id) ON DELETE CASCADE,
                mutant_index   INTEGER NOT NULL,
                mutant_path    TEXT NOT NULL UNIQUE,
                build_status   TEXT NOT NULL DEFAULT 'pending'
                               CHECK (build_status IN ('pending','survived','killed')),
                UNIQUE (source_file_id, mutant_index)
            );

            CREATE INDEX IF NOT EXISTS idx_mutants_source ON mutants(source_file_id);
            CREATE INDEX IF NOT EXISTS idx_mutants_status ON mutants(build_status);

            CREATE TABLE IF NOT EXISTS mutant_density_per_line (
                source_file_id INTEGER NOT NULL REFERENCES source_files(id) ON DELETE CASCADE,
                line_number    INTEGER NOT NULL,
                mutant_count   INTEGER NOT NULL,
                PRIMARY KEY (source_file_id, line_number)
            );

            CREATE TABLE IF NOT EXISTS complexity_per_method (
                source_file_id INTEGER NOT NULL REFERENCES source_files(id) ON DELETE CASCADE,
                method_name    TEXT NOT NULL,
                density        INTEGER NOT NULL,
                cyclomatic     INTEGER NOT NULL,
                lines_of_code  INTEGER NOT NULL,
                PRIMARY KEY (source_file_id, method_name)
            );
            """
        )
        self.connection.commit()

    def add_source_file(self, source_path):
        """
        Idempotently inserts a source file and returns its row id.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO source_files (path) VALUES (?)", (source_path,))
        cursor.execute(
            "SELECT id FROM source_files WHERE path = ?", (source_path,))
        row = cursor.fetchone()
        self.connection.commit()
        return row[0]

    def add_mutant(self, source_path, mutant_index, mutant_path):
        """
        Inserts a mutant row for ``source_path`` with ``build_status='pending'``.
        Upserts the parent source_files row first.
        """
        source_id = self.add_source_file(source_path)
        self.connection.execute(
            "INSERT INTO mutants (source_file_id, mutant_index, mutant_path) VALUES (?, ?, ?)",
            (source_id, int(mutant_index), mutant_path))
        self.connection.commit()

    def record_result(self, mutant_path, status):
        """
        Flips ``mutant_path``'s ``build_status`` to ``status`` (``'survived'``
        or ``'killed'``). Re-recording overwrites the previous value.
        """
        if status not in ("survived", "killed"):
            raise ValueError("status must be 'survived' or 'killed', got: " + repr(status))
        cursor = self.connection.execute(
            "UPDATE mutants SET build_status = ? WHERE mutant_path = ?",
            (status, mutant_path))
        if cursor.rowcount == 0:
            raise KeyError(mutant_path)
        self.connection.commit()

    def record_line_densities(self, source_path, densities):
        """
        Replaces the per-line mutant counts for ``source_path``.

        :param densities: Iterable of ``(line_number, mutant_count)`` pairs.
        """
        source_id = self.add_source_file(source_path)
        rows = [(source_id, int(line), int(count)) for line, count in densities]
        self.connection.execute(
            "DELETE FROM mutant_density_per_line WHERE source_file_id = ?", (source_id,))
        self.connection.executemany(
            "INSERT INTO mutant_density_per_line (source_file_id, line_number, mutant_count) VALUES (?, ?, ?)",
            rows)
        self.connection.commit()

    def record_method_complexities(self, source_path, complexities):
        """
        Replaces the per-method complexity rows for ``source_path``.

        :param complexities: Iterable of
            ``(method_name, density, cyclomatic, lines_of_code)`` tuples.
        """
        source_id = self.add_source_file(source_path)
        rows = [(source_id, name, int(density), int(cyclomatic), int(loc))
                for name, density, cyclomatic, loc in complexities]
        self.connection.execute(
            "DELETE FROM complexity_per_method WHERE source_file_id = ?", (source_id,))
        self.connection.executemany(
            "INSERT INTO complexity_per_method "
            "(source_file_id, method_name, density, cyclomatic, lines_of_code) "
            "VALUES (?, ?, ?, ?, ?)",
            rows)
        self.connection.commit()

    def source_paths(self):
        """
        Returns the list of source-file paths that have at least one mutant.
        """
        return [row[0] for row in self.connection.execute(
            "SELECT s.path FROM source_files s "
            "WHERE EXISTS (SELECT 1 FROM mutants m WHERE m.source_file_id = s.id)")]

    def mutants_for(self, source_path):
        """
        Returns the mutant relative paths for ``source_path``, ordered by
        mutant_index. Empty list if the source is unknown or has no mutants.
        """
        return [row[0] for row in self.connection.execute(
            "SELECT m.mutant_path FROM mutants m "
            "JOIN source_files s ON s.id = m.source_file_id "
            "WHERE s.path = ? ORDER BY m.mutant_index", (source_path,))]

    def mutant_count_for(self, source_path):
        """
        Returns the number of mutants registered for ``source_path``.
        """
        row = self.connection.execute(
            "SELECT COUNT(*) FROM mutants m "
            "JOIN source_files s ON s.id = m.source_file_id "
            "WHERE s.path = ?", (source_path,)).fetchone()
        return row[0]

    def results_for(self, source_path):
        """
        Returns ``(survived_basenames, killed_basenames)`` for ``source_path``,
        each list ordered by mutant_index. Pending mutants are excluded.
        """
        rows = self.connection.execute(
            "SELECT m.mutant_path, m.build_status FROM mutants m "
            "JOIN source_files s ON s.id = m.source_file_id "
            "WHERE s.path = ? ORDER BY m.mutant_index", (source_path,))
        survived = []
        killed = []
        for mutant_path, status in rows:
            if status == "survived":
                survived.append(os.path.basename(mutant_path))
            elif status == "killed":
                killed.append(os.path.basename(mutant_path))
        return survived, killed

    def close(self):
        """
        Commits any pending changes and closes the underlying connection.
        """
        if self.connection is not None:
            self.connection.commit()
            self.connection.close()
            self.connection = None

    def __enter__(self):
        return self

    def __exit__(self, excType, excValue, traceback):
        self.close()
