#!/usr/bin/env python
# coding: utf-8
from setuptools import setup, find_packages
from elasticindex import __author__, __version__, __license__

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
