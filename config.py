# -*-coding=UTF-8-*-
"""Config file on disk.  """

import os
import json

__version__ = '0.2.0'


class Config(dict):
    """Comp config.  """
    default = {}
    path = os.path.expanduser(u'~/wlf.config.json')
    instance = None

    def __new__(cls):
        if not cls.instance:
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        super(Config, self).__init__()
        self.update(dict(self.default))
        self.read()

    def __str__(self):
        return json.dumps(self)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.write()

    def write(self):
        """Write config to disk.  """

        with open(self.path, 'w') as f:
            json.dump(self, f, indent=4, sort_keys=True)

    def read(self):
        """Read config from disk.  """

        if os.path.isfile(self.path):
            with open(self.path) as f:
                self.update(dict(json.load(f)))
