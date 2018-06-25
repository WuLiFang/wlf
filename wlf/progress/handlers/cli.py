# -*- coding=UTF-8 -*-
"""CLI progress handler.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

import six

from .. import core
from ...codectools import get_unicode as u
from .base import BaseProgressHandler


class CLIProgressHandler(BaseProgressHandler):
    """Command line progress bar.

    reference with: https://github.com/noamraph/tqdm
    """

    def __init__(self, **handler_kwargs):
        super(CLIProgressHandler, self).__init__(**handler_kwargs)
        self.file = handler_kwargs.get('file', sys.stdout)
        self.last_printed_len = 0

    def set_message(self, message):
        message = u(message)
        encoding = sys.getfilesystemencoding()
        try:
            encoding = self.file.encoding or encoding
        except AttributeError:
            pass
        msg_len = len(message.encode(encoding))
        msg = ('\r' + message
               + ' ' * max(self.last_printed_len - msg_len, 0))

        if six.PY2:
            msg = msg.encode(encoding, 'replace')
        self.file.write(msg)
        self.file.flush()
        self.last_printed_len = msg_len

    def message_factory(self, item):
        return '[{}/{}]{}%{}'.format(self.count, self.total, self.count * 100 / self.total, item)


core.DefaultHandler = CLIProgressHandler
