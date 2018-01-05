# -*- coding=UTF-8 -*-
"""History task info database.  """

import sqlite3
from datetime import datetime, timedelta
from logging import getLogger
from multiprocessing import Lock
from os.path import expanduser
from contextlib import contextmanager
from ..cgtwq import Shots
LOGGER = getLogger('database')


class Database(object):
    """Database for rendering.  """

    expire_days = 30

    def __init__(self, path):

        self.path = path
        self.lock = Lock()

        # Init tables.
        tables = {
            'shot': 'name, image, preview, thumb, timestamp',
        }
        with self.connection() as conn:
            c = conn.cursor()
            for table, fileds in tables.items():
                try:
                    c.execute("SELECT {} FROM {}".format(fileds, table))
                    # Drop old records.
                    c.execute(
                        "DELETE FROM {} where timestamp < ? ".format(table),
                        (datetime.now() - timedelta(days=self.expire_days),))
                    conn.commit()
                except sqlite3.OperationalError as ex:
                    try:
                        LOGGER.warning(
                            "Can not reconize table, reset: %s", table)
                        c.execute("DROP TABLE {}".format(table))
                    except sqlite3.OperationalError:
                        pass
                    c.execute(
                        "CREATE TABLE {} ({})".format(table, fileds))
                    conn.commit()

    def __getitem__(self, name):
        return DatabaseTable(name, self)

    @contextmanager
    def connection(self):
        """Return connection object for this.  """

        with self.lock:
            conn = sqlite3.connect(self.path)
            try:
                yield conn
            finally:
                conn.close()

    def get_image(self, filename, frame):
        """Get frame time cost for @filename at @frame.  """

        with self.connection() as conn:
            c = conn.cursor()
            c.execute("SELECT cost "
                      "FROM frames "
                      "WHERE filename=? AND frame=? "
                      "ORDER BY timestamp DESC",
                      (filename, frame))
            ret = c.fetchone()
        return ret[0] if ret else None

    def get_preview(self, filename):
        """Get averge frame time cost for @filename.  """

        with self.connection() as conn:
            c = conn.cursor()
            c.execute("SELECT avg(cost) "
                      "FROM frames "
                      "WHERE filename=?",
                      (filename,))
            ret = c.fetchone()[0]
        return ret

    def update_shots(self, shots):
        """Set frame time cost for @filename at @frame.  """

        assert isinstance(shots, Shots)
        shots.get_shot_image
        with self.connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO frames VALUES (?,?,?,?)", (filename, frame, cost, datetime.now()))
            conn.commit()
            # LOGGER.debug('Set: %s %s %s', filename, frame, cost)


class DatabaseTable(object):
    """Table in database"""

    def __init__(self, name, database):
        assert isinstance(database, Database)
        self.name = name
        self.database = database

    def __getitem__(self, name):
        return TableItem(name, self)


class TableItem(object):
    """Item in table"""

    def __init__(self, name, table):
        assert isinstance(table, DatabaseTable)
        self.name = name
        self.table = table

    def __setattr__(self, name, value):
        with self.connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * "
                      "FROM tasks "
                      "WHERE name=?", (self.name,))
            if c.fetchone():
                c.execute(("UPDATE {} "
                           "SET {}=?, timestamp=?"
                           "WHERE name=?").format(self.table.name, name), (value, datetime.now(), self.name))
            else:
                c.execute(
                    "INSERT INTO {} (name, {}, timestamp) VALUES (?,?,?)".format(
                        self.table.name, name),
                    (self.name, value, datetime.now()))
            conn.commit()

    def __getattribute__(self, name):
        with self.table.database.connection() as conn:
            c = conn.cursor()
            c.execute("SELECT avg(cost) "
                      "FROM {} "
                      "WHERE name=?".format(self.table),
                      (self.name,))
            ret = c.fetchone()[0]
        return ret


DATABASE = Database(expanduser('~/.wlf/csheet.db'))
