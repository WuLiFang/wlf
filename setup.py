"""Python setup script.  """
import os

from setuptools import find_packages, setup

__about__ = {}
with open(os.path.join(os.path.dirname(__file__),
                       'wlf', '__about__.py')) as f:
    exec(f.read(), __about__)  # pylint: disable=exec-used

REQUIRES = [
    'psutil~=5.4',
    'qt.py~=1.1',
    "pathlib2~=2.3;python_version<'3'",
    "six~=1.12"
]

setup(
    name='wlf',
    version=__about__['__version__'],
    author=__about__['__author__'],
    packages=find_packages(),
    package_data={'': ['data/*.json', 'assets/*.png', 'assets/*.ui']},
    install_requires=REQUIRES
)
