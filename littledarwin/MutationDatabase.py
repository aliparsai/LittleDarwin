import os
import pickle
import sqlite3


class MutationDatabase(object):
    """
    A persistent key-value store backed by SQLite.

    This replaces the previous ``shelve``-based storage. ``shelve`` relies on
    the platform's ``dbm`` backend, so the resulting database file format
    differs between operating systems and Python builds and cannot be moved
    between them. SQLite produces a single, self-contained, cross-platform file
    instead.

    Keys are strings (relative file paths). Values are arbitrary picklable
    Python objects (for example a list of mutant file paths, or a tuple of the
    survived and killed mutant lists).
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
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS entries (key TEXT PRIMARY KEY, value BLOB)")
        self.connection.commit()

    def set(self, key, value):
        """
        Stores ``value`` under ``key``, overwriting any existing entry.

        :param key: The entry key.
        :type key: str
        :param value: Any picklable Python object.
        """
        blob = sqlite3.Binary(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        self.connection.execute(
            "INSERT OR REPLACE INTO entries (key, value) VALUES (?, ?)", (key, blob))
        self.connection.commit()

    def get(self, key):
        """
        Returns the value stored under ``key``.

        :param key: The entry key.
        :type key: str
        :return: The previously stored Python object.
        :raises KeyError: if the key is not present (mirrors ``db[key]``).
        """
        row = self.connection.execute(
            "SELECT value FROM entries WHERE key = ?", (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        return pickle.loads(row[0])

    def keys(self):
        """
        Returns the list of all keys in the database.

        :rtype: list
        """
        return [row[0] for row in self.connection.execute("SELECT key FROM entries")]

    def __contains__(self, key):
        return self.connection.execute(
            "SELECT 1 FROM entries WHERE key = ?", (key,)).fetchone() is not None

    def __len__(self):
        return self.connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

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
