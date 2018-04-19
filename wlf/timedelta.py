# -*- coding=UTF-8 -*-
"""Timedelta parse and string format.

>>> strf_timedelta(parse_timedelta('1:3.25'))
'0:01:03.25'
>>> print(strf_timedelta(parse_timedelta('1天2小时')))
1 天, 2:00:00
>>> print(strf_timedelta(parse_timedelta('1 天, 2:34:56.789')))
1 天, 2:34:56.789
>>> print(strf_timedelta(parse_timedelta('1天25小时2分13.2秒3毫秒4微秒')))
2 天, 1:02:13.203004
"""

from __future__ import unicode_literals, print_function

import datetime
import re


__version__ = '0.1.3'


def parse_timedelta(text):
    """Parse timedelta.  """
    match = re.match(
        r'(?:(\d+(?:\.\d+)?)\s*天)?(?:(\d+(?:\.\d+)?)\s*小?时)?'
        r'(?:(\d+(?:\.\d+)?)\s*分钟?)?(?:(\d+(?:\.\d+)?)\s*秒)?'
        r'(?:(\d+(?:\.\d+)?)\s*毫秒)?(?:(\d+(?:\.\d+)?)\s*微秒)?'
        r'\s*,?\s*(?:(\d?\d)??:?(?:(\d?\d)??:?(\d?\d(?:\.\d+)??)))?\s*$', text)
    if not match:
        raise ValueError('Timedelta format can not recognize: %s' % text)
    result = [float(i) if i else 0 for i in match.groups()]
    return datetime.timedelta(days=result[0],
                              hours=result[1] or result[6],
                              minutes=result[2]or result[7],
                              seconds=result[3]or result[8],
                              milliseconds=result[4],
                              microseconds=result[5])


def strf_timedelta(timedelta):
    """String format timedelta.  """
    ret = re.sub('days?', '天', str(timedelta))
    ret = re.sub(r'(\.\d*?)0+$', r'\1', ret)
    return ret
