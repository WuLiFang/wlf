# -*- coding=UTF-8 -*-
"""Console operation"""

import sys
import time
from subprocess import call

__version__ = '0.1.0'


def pause(timeout=5):
    """Pause prompt with a countdown."""

    if timeout <= 0:
        if sys.platform == 'win32':
            call('PAUSE', shell=True)
    else:
        print(u'')
        for i in range(timeout)[::-1]:
            sys.stdout.write(u'\r{:2d}'.format(i + 1))
            time.sleep(1)
        sys.stdout.write(u'\r          ')
        print(u'')
