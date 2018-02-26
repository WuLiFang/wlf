# -*- coding=UTF-8 -*-
"""Test `decorators` module.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import main, TestCase
from functools import partial
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

    def test_deprecated(self):
        from wlf.decorators import deprecated

        @deprecated('test1')
        def func():  # pylint: disable=unused-variable
            "test1 doc"
            pass

        @deprecated('test2')
        class test2(object):
            "test2 doc"
            pass

        @deprecated
        def test3():
            "test3 doc"
            pass

        @deprecated
        class test4(object):
            "test4 doc"
            pass

        # pylint: disable=undefined-variable
        self.assertEqual(test1.__doc__, 'test1 doc')
        self.assertEqual(test2.__doc__, 'test2 doc')
        self.assertEqual(test3.__doc__, 'test3 doc')
        self.assertEqual(test4.__doc__, 'test4 doc')
        self.assertEqual(test1.__name__, 'test1')
        self.assertEqual(test2.__name__, 'test2')
        self.assertEqual(test3.__name__, 'test3')
        self.assertEqual(test4.__name__, 'test4')
        fail = partial(self.assert_, 0, 'DeprecationWarning not raised.')
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            try:
                test1()
                fail()
            except DeprecationWarning:
                pass
            try:
                test2()
                fail()
            except DeprecationWarning:
                pass
            try:
                test3()
                fail()
            except DeprecationWarning:
                pass
            try:
                test4()
                fail()
            except DeprecationWarning:
                pass


if __name__ == '__main__':
    main()
