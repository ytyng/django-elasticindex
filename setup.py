#!/usr/bin/env python
# coding: utf-8
from setuptools import setup, find_packages
from jj_menu import __author__, __version__, __license__

# In [2]: from setuptools.command.bdist_egg import _get_purelib
#
# In [3]: _get_purelib()
# Out[3]: '/Users/yotsuyanagi/.virtualenvs/default/lib/python2.7/site-packages'
# $ cd $(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"

setup(
    name='django-elasticindex',
    version=__version__,
    description='Elasticsearch Accessor (Django like)',
    license=__license__,
    author=__author__,
    author_email='ytyng@live.jp',
    url='https://github.com/ytyng/elasticindex.git',
    keywords='Elasticsearch, Django, Python',
    packages=find_packages(),
    install_requires=['elasticsearch', 'requests_aws4auth'],
    entry_points={
    },
)
