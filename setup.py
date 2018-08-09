"""Python setup script.  """
import os
import sys

from setuptools import find_packages, setup

__about__ = {}
with open(os.path.join(os.path.dirname(__file__),
                       'wlf', '__about__.py')) as f:
    exec(f.read(), __about__)  # pylint: disable=exec-used

REQUIRES = [
    'psutil>=5.4.3',
    'qt.py>=1.1.0',
]
if sys.version.startswith('2.'):
    REQUIRES.append('pathlib2>=2.3.0')

setup(
    name='wlf',
    version=__about__['__version__'],
    author=__about__['__author__'],
    packages=find_packages(),
    package_data={'': ['data/*.json', 'assets/*.png', 'assets/*.ui']},
    install_requires=REQUIRES
)
