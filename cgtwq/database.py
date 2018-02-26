# -*- coding=UTF-8 -*-
"""Database in cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from .module import Module


class Database(object):
    def __init__(self, name):
        self.name = name

    def get_module(self,name):
        return Module(name, database=self)
