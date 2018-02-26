# -*- coding=UTF-8 -*-
"""Test `decorators` module.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import main, TestCase
import warnings


class DecoratorTestCase(TestCase):

    def test_renamed(self):
        from wlf.decorators import renamed

        @renamed('test1_old')
        def test1():
            return 'test1'

        @renamed('Test2_old')
        class Test2(object):
            pass

            def __init__(self):
                self.data = 'test2_data'

            def method(self):
                return self.data

        # pylint: disable=undefined-variable
        self.assertEqual(test1(), test1_old())
        self.assertIs(Test2_old, Test2)
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            test1()
            Test2()
            try:
                Test2_old()
                self.assert_(0, 'DeprecationWarning not raised.')
            except DeprecationWarning:
                pass
            try:
                test1_old()
                self.assert_(0, 'DeprecationWarning not raised.')
            except DeprecationWarning:
                pass


if __name__ == '__main__':
    main()
