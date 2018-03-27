"""Python setup script.  """
import sys
from setuptools import setup, find_packages

sys.path.insert(0, 'wlf')
__about__ = __import__('__about__')

setup(
    name='wlf',
    version=__about__.__version__,
    author=__about__.__author__,
    packages=find_packages(),
    package_data={'': ['*.json', '*.png', '*.ui']},
    install_requires=[
        'pathlib2==2.3.0',
        'gevent==1.2.2',
        'openpyxl==2.5.1',
        'psutil==5.4.3',
        'beautifulsoup4==4.6.0',
        'qt.py==1.1.0',
        'pyblish==1.4.3',
    ]
)
