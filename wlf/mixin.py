# -*- coding=UTF-8 -*-
"""Mixin class.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# pylint: disable=too-few-public-methods


class SingletonMixin(object):
    """Provide `instance` class method that always return same instance.  """
    _instance = None

    @classmethod
    def instance(cls):
        """Return single instance.  """

        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
