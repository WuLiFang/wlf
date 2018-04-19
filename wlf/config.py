# -*-coding=UTF-8-*-
"""Config file on disk.  """

from __future__ import absolute_import, print_function, unicode_literals

import json
import os

from .path import Path, get_unicode as u


class Config(dict):
    """Comp config.  """

    default = {}
    path = os.path.expanduser(u'~/wlf.config.json')

    def __init__(self):
        super(Config, self).__init__(self.default)

    def __str__(self):
        self.read()
        return json.dumps(self)

    def __setitem__(self, key, value):
        self.read()
        dict.__setitem__(self, key, value)
        self.write()

    def __getitem__(self, key):
        self.read()
        return dict.__getitem__(self, key)

    def write(self):
        """Write config to disk.  """

        path = Path(self.path)
        try:
            Path(path.parent).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        with path.open('w', encoding='utf-8') as f:
            data = json.dumps(self, indent=4, sort_keys=True)
            f.write(u(data))

    def read(self):
        """Read config from disk.  """

        path = Path(self.path)
        try:
            with path.open(encoding='utf-8') as f:
                self.update(dict(json.load(f)))
        except (ValueError, IOError):
            pass

        return self
