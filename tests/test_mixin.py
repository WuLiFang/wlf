# -*- coding=UTF-8 -*-
"""Test module `mixin`.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from wlf import mixin


def test_singleton():
    class TestClass(list, mixin.SingletonMixin):
        """Test class.  """

    assert TestClass.instance() == TestClass.instance()
