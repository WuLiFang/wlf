"""Python setup script.  """
import os
import sys

from setuptools import find_packages, setup

__about__ = {}
with open(os.path.join(os.path.dirname(__file__),
                       'wlf', '__about__.py')) as f:
    exec(f.read(), __about__)  # pylint: disable=exec-used

REQUIRES = [
    'openpyxl>=2.5.1',
    'psutil>=5.4.3',
    'beautifulsoup4>=4.6.0',
    'qt.py>=1.1.0',
]
if sys.version.startswith('2.'):
    REQUIRES.append('pathlib2>=2.3.0')

setup(
    name='wlf',
    version=__about__['__version__'],
    author=__about__['__author__'],
    packages=find_packages(),
    package_data={'': ['*.json', '*.png', '*.ui']},
    install_requires=REQUIRES
)
