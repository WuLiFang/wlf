"""Python setup script.  """
from setuptools import setup, find_packages
from wlf import __about__

setup(
    name='wlf',
    version=__about__.__version__,
    author=__about__.__author__,
    packages=find_packages(),
    package_data={'': ['*.json', '*.png', '*.ui']},
)
