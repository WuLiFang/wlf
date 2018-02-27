"""Test wlf.table module."""
from unittest import TestCase

from wlf.table import NestedData


class TableTestCase(TestCase):
    test_list_data = ['A1', {'B1': ['C1', 'C2']},
                      'D1', {'E1': {'E2': [{'E3': 1}, {'F3': 2}]}}]
    test_tuple_data = ('A1', ('B1', ('C1', 'C2')), 'D1',
                       ('E1', ('E2', ('E3', ))), ('E1', ('E2', ('F3',))))
    test_mixed_data = ['A1', {'B1': ['C1', 'C2']},
                       'D1', ('E1', ('E2', ('E3', ))), ('E1', ('E2', ('F3',)))]

    def test_list(self):
        data = NestedData(self.test_list_data)
        self.assertEqual(data.to_columns(), [['A1'], ['B1', 'C1'], ['B1', 'C2'],
                                             ['D1'], ['E1', 'E2', 'E3', 1], ['E1', 'E2', 'F3', 2]])
        self.assertEqual(data.to_rows(), [['A1', 'B1', 'B1', 'D1', 'E1', 'E1'],
                                          [None, 'C1', 'C2', None, 'E2', 'E2'],
                                          [None, None, None, None, 'E3', 'F3'],
                                          [None, None, None, None, 1, 2]])
        self.assertEqual(data.to_tuple(), (('B1', ('C1',)), ('B1', ('C2',)),
                                           ('E1', ('E2', ('E3', (1,)))),
                                           ('E1', ('E2', ('F3', (2,))))))
        self.assertEqual(data.to_dict(),
                         {('B1',): 'C2',
                          ('E1', ('E2', ('E3',))): 1,
                          ('E1', ('E2', ('F3',))): 2})

    def test_tuple(self):
        data = NestedData(self.test_tuple_data)
        self.assertEqual(data.to_columns(), [['A1'], ['B1', 'C1'], ['B1', 'C2'],
                                             ['D1'], ['E1', 'E2', 'E3'], ['E1', 'E2', 'F3']])
        self.assertEqual(data.to_rows(), [['A1', 'B1', 'B1', 'D1', 'E1', 'E1'],
                                          [None, 'C1', 'C2', None, 'E2', 'E2'],
                                          [None, None, None, None, 'E3', 'F3']])
        self.assertEqual(data.to_tuple(), (('B1', ('C1',)), ('B1', ('C2',)),
                                           ('E1', ('E2', ('E3',))), ('E1', ('E2', ('F3',)))))
        self.assertEqual(data.to_dict(), {
                         ('B1',): 'C2', ('E1', ('E2',)): 'F3'})

    def test_mixed(self):
        data = NestedData(self.test_mixed_data)
        self.assertEqual(data.to_columns(), [['A1'], ['B1', 'C1'], ['B1', 'C2'],
                                             ['D1'], ['E1', 'E2', 'E3'], ['E1', 'E2', 'F3']])
        self.assertEqual(data.to_rows(), [['A1', 'B1', 'B1', 'D1', 'E1', 'E1'],
                                          [None, 'C1', 'C2', None, 'E2', 'E2'],
                                          [None, None, None, None, 'E3', 'F3']])
        self.assertEqual(data.to_tuple(), (('B1', ('C1',)), ('B1', ('C2',)),
                                           ('E1', ('E2', ('E3',))), ('E1', ('E2', ('F3',)))))
        self.assertEqual(data.to_dict(), {('B1',): 'C2',
                                          ('E1', ('E2',)): 'F3'})
