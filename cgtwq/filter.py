# -*- coding=UTF-8 -*-
"""Filter used on cgtw server.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


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
