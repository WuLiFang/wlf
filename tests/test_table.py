"""Test wlf.table module."""
from unittest import TestCase
from pprint import pprint

from wlf.table import NestedData


class TableTestCase(TestCase):
    test_list_data = ['A1', {'B1': ['C1', 'C2']},
                      'D1', {'E1': {'E2': [{'E3': 1}, {'F3': 2}]}}]
    test_tuple_data = ('A1', ('B1', ('C1', 'C2')), 'D1',
                       ('E1', ('E2', ('E3', ))), ('E1', ('E2', ('F3',))))
    test_mixed_data = ['A1', {'B1': ['C1', 'C2']},
                       'D1', ('E1', ('E2', ('E3', ))), ('E1', ('E2', ('F3',)))]

    def test_list(self):
        print('testing list data')
        data = NestedData(self.test_list_data)
        print(data.to_columns())
        pprint(data.to_rows())
        print(data.to_tuple())
        print(data.to_dict())

    def test_tuple(self):
        print('testing tuple data')
        data = NestedData(self.test_tuple_data)
        print(data.to_columns())
        pprint(data.to_rows())
        print(data.to_tuple())
        print(data.to_dict())

    def test_mixed(self):
        print('testing mixed data')
        data = NestedData(self.test_mixed_data)
        print(data.to_columns())
        pprint(data.to_rows())
        print(data.to_tuple())
        print(data.to_dict())
