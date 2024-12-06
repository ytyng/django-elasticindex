from pathlib import Path

from setuptools import setup

from elasticindex import __author__, __license__, __version__

this_directory = Path(__file__).parent
long_description = (this_directory / 'README.rst').read_text()

setup(
    name='django-elasticindex',
    version=__version__,
    description='Shallow elasticsearch wrapper on Django',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license=__license__,
    author=__author__,
    author_email='ytyng@live.jp',
    url='https://github.com/ytyng/django-elasticindex',
    keywords='Elasticsearch, Django, Python',
    packages=['elasticindex'],
    install_requires=['elasticsearch', 'requests_aws4auth'],
    entry_points={},
)
