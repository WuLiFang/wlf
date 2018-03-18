"""Docstring test.  """
from __future__ import absolute_import
from unittest import TestCase, skipIf
import doctest
import six


@skipIf(six.PY3, 'Docstrings is wrote for python2.')
class DocstringTestCase(TestCase):
    def _test_mod(self, mod):
        result = doctest.testmod(mod, verbose=False)
        self.assertFalse(result.failed)

    def test_path(self):
        from wlf import path
        self._test_mod(path)

    def test_file(self):
        from wlf import files
        self._test_mod(files)

    def test_timedelta(self):
        from wlf import timedelta
        self._test_mod(timedelta)
