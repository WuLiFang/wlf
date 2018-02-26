# -*- coding=UTF-8 -*-
"""Module(table) in cgtw database.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from collections import Iterable
from . import server


class Selection(list):
    def __init__(self, id_list, module):
        super(Selection, self).__init__(id_list)
        self.module = module


class Filter(list):
    """CGteamwork style filter.  """

    def __init__(self, key, value):
        super(Filter, self).__init__([key, '=', value])

    def __and__(self, other):
        return FilterList(self) & FilterList(other)

    def __or__(self, other):
        return FilterList(self) | FilterList(other)


class FilterList(list):
    """CGteamwork style filter list.  """

    def __init__(self, list_):
        assert isinstance(list_, (Filter, FilterList)), type(list_)
        if isinstance(list_, Filter):
            list_ = [list_]
        super(FilterList, self).__init__(list_)

    def __and__(self, other):
        ret = FilterList(self)
        ret.append('and')
        ret += FilterList(other)
        return ret

    def __or__(self, other):
        ret = FilterList(self)
        ret.append('or')
        ret += FilterList(other)
        return ret


class Module(object):
    def __init__(self, name, database):
        self.name = name
        self.database = database

    def select(self, id_list):
        assert isinstance(id_list, list)
        return Selection(id_list, self)

    def filter(self, filters):
        if isinstance(filters, Filter):
            filters = FilterList(filters)
        assert isinstance(filters, FilterList), type(filters)
        resp = server.send('c_orm', 'get_with_filter',
                           {'db': self.database.name,
                            'sign_array': self.name+'.id',
                            'sign_filter_array': filters})
        id_list = resp.data
        return self.select(id_list)

    # TODO: test.
    def message(self, from_, to, title, content, task_id):
        """Send message to users.  """
        return server.send(
            'c_msg', 'send_task',
            {"db": self.database.name,
             "module": self.name,
             "task_id": task_id,
             "account_id_array": to,
             "title": title,
             "content": content,
             "from_account_id": from_}
        )


if __name__ == '':
    import cgtw
