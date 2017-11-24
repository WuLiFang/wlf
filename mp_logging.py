# -*- coding=UTF-8 -*-
"""Handle logging with multiprocessing.  """
from __future__ import print_function, unicode_literals

import logging
import multiprocessing
import multiprocessing.dummy
import sys
import os
import traceback

__verion__ = '0.1.1'


class Handler(multiprocessing.dummy.Process):
    """Multiprocessing adapted handler.  """

    def __init__(self, handler, args=(), kwargs=None):
        assert issubclass(handler, logging.Handler)

        kwargs = kwargs or {}
        self._handler = handler(*args, **kwargs)
        self.queue = multiprocessing.Queue(-1)

        super(Handler, self).__init__(name=handler.get_name(self._handler))

        self.daemon = True
        self.start()

    def __getattr__(self, name):
        return getattr(self._handler, name)

    def run(self):
        while True:
            try:
                record = self.queue.get()
                self._handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                traceback.print_exc(file=sys.stderr)

    def _format_record(self, record):
        # ensure that exc_info and args
        # have been stringified.  Removes any chance of
        # unpickleable things inside and possibly reduces
        # message size sent over the pipe
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            self.format(record)
            record.exc_info = None

        return record

    def emit(self, record):
        """(override)logging.handler.emit  """

        try:
            msg = self._format_record(record)
            self.queue.put_nowait(msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        """(override)logging.handler.close  """

        self._handler.close()


def set_basic_logger(logger=None):
    """Basic log setting.  """

    logger = logger or logging.getLogger()
    logger.propagate = False

    # Loglevel
    loglevel = os.getenv('LOGLEVEL', logging.INFO)
    try:
        logger.setLevel(int(loglevel))
    except TypeError:
        logging.warning(
            'Can not recognize env:LOGLEVEL %s, expect a int', loglevel)

    # Stream handler
    handler = Handler(logging.StreamHandler)
    if logger.getEffectiveLevel() == logging.DEBUG:
        formatter = logging.Formatter(
            '%(levelname)-6s[%(asctime)s]:%(filename)s:'
            '%(lineno)d:%(funcName)s: %(message)s', '%H:%M:%S')
    else:
        formatter = logging.Formatter(
            '%(levelname)-6s[%(asctime)s]:'
            '%(name)s: %(message)s', '%H:%M:%S')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.debug('Basic logger set finish.')
