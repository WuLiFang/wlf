"""Python setup script.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from setuptools import setup, find_packages
import __about__
setup(
    name='wlf',
    version=__about__.__version__,
    author=__about__.__author__,
    package=find_packages(),
    package_data={
        '': ['*.json', '*.png'],
    },
)
