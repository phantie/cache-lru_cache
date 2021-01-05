"""Build with
   > py setup.py sdist"""

from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    author = 'phantie',
    name = 'rcache',
    version = '0.1',
    packages = find_packages(),
    long_description = open(join(dirname(__file__), 'README.md')).read(),
    install_requires=[
            'bmap @ https://github.com/phantie/bound-sized-hash-map/archive/0.4.tar.gz',
        ]
)