#!/usr/bin/env python
# coding: utf-8
import os
import sys
from os.path import dirname, abspath
import django
from django.conf import settings

SETTINGS = {
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }
    },
    'INSTALLED_APPS': [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'elasticindex',
        'tests',
    ],
    'MIDDLEWARE_CLASSES': (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ),
    'SITE_ID': 1,
    'DEBUG': False,
    'ROOT_URLCONF': '',
    'ELASTICINDEX_HOSTS': [{'host': '127.0.0.1', 'port': 9200}]
}


def runtests(**test_args):
    if os.path.exists('local_settings.py'):
        import local_settings
        for k, v in vars(local_settings).items():
            if k.isupper():
                SETTINGS[k] = v

    settings.configure(**SETTINGS)

    from django.test.utils import get_runner

    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)

    django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(['tests'], test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])
