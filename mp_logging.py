# -*- coding=UTF-8 -*-
"""Handle logging with multiprocessing.  """
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
import sys
import traceback
import warnings
from multiprocessing.dummy import Lock, Process, Queue

from six import text_type

from .decorators import renamed

_LOCK = Lock()


class Handler(Process):
    """Multiprocessing adapted handler.  """

    def __init__(self, handler, args=(), **kwargs):
        assert issubclass(handler, logging.Handler)

        self._handler = handler(*args, **kwargs)
        # Patch for use non default encoding.
        if issubclass(handler, logging.StreamHandler):
            def _format(record):
                def _encode(i):
                    if isinstance(i, text_type):
                        try:
                            return i.encode(sys.stdout.encoding, 'replace')
                        except:  # pylint: disable=bare-except
                            pass
                    return i
                record.msg = _encode(record.msg)
                record.args = tuple(_encode(i) for i in record.args)
                ret = handler.format(self._handler, record)
                return ret
            self._handler.format = _format
        self.queue = Queue(-1)

        super(Handler, self).__init__(name=str(self._handler))

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
            except:  # pylint:disable=bare-except
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
        except:  # pylint:disable=bare-except
            self.handleError(record)

    def close(self):
        """(override)logging.handler.close  """

        self._handler.close()


@renamed('set_basic_logger')
def basic_config(*args, **kwargs):  # pylint: disable=unused-argument
    """Optmized logging.basicConfig.  """

    # Set warnings.
    warnings.simplefilter('module', DeprecationWarning)
    logging.captureWarnings(True)

    if 'level' in kwargs:
        loglevel = kwargs['level']
    else:
        try:
            loglevel = int(os.getenv('LOGLEVEL'))
        except TypeError:
            loglevel = None

    _kwargs = {
        'level': loglevel,
        'format': (b'%(levelname)-6s[%(asctime)s]:%(filename)s:%(lineno)d:%(funcName)s: %(message)s'
                   if loglevel == logging.DEBUG
                   else b'%(levelname)-6s[%(asctime)s]:%(name)s: %(message)s'),
        'datafmt':  b'%H:%M:%S'
    }
    _kwargs.update(kwargs)
    kwargs = _kwargs

    with _LOCK:
        if not logging.root.handlers:
            filename = kwargs.get("filename")
            if filename:
                mode = kwargs.get("filemode", 'a')
                hdlr = Handler(logging.FileHandler, (filename, mode))
            else:
                stream = kwargs.get("stream")
                hdlr = Handler(logging.StreamHandler, (stream,))
            fms = kwargs.get("format", logging.BASIC_FORMAT)
            dfs = kwargs.get("datefmt", None)
            fmt = logging.Formatter(fms, dfs)
            hdlr.setFormatter(fmt)
            logging.root.addHandler(hdlr)
            level = kwargs.get("level")
            if level is not None:
                logging.root.setLevel(level)

            logging.debug('Set basic logging config.')
