# -*- coding=UTF-8 -*-
"""Data table"""

from __future__ import print_function, unicode_literals
from openpyxl import Workbook


class RowTable(object):
    """Table based on row.  """

    def __init__(self, rows=None, header=None):
        self.header = header or []
        self.rows = []
        if rows:
            for row in rows:
                self.append(row)

    def append(self, row):
        """Append row to table.  """

        assert isinstance(row, dict), row
        self.rows.append(row)
        for key in row.keys():
            if key not in self.header:
                self.header.append(key)

    def to_html(self, filename):
        # TODO
        pass

    def to_xlsx(self, filename):
        """Demp table to xlsx sheet.  """

        book = Workbook(write_only=True)
        sheet = book.create_sheet()
        sheet.append(self.header)
        for row in self.rows:
            sheet_row = [row.get(i) for i in self.header]
            sheet.append(sheet_row)
        book.save(filename)
