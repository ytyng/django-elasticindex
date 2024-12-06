"""
docker run --rm -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:7.9.3
"""

import os
import sys
from os.path import abspath, dirname

import django
from django.conf import settings

SETTINGS = {
    'DATABASES': {
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
    },
    'INSTALLED_APPS': [
        'elasticindex',
        'tests',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.sites',
    ],
    'MIDDLEWARE': (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ),
    'TEMPLATES': [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'social_django.context_processors.backends',
                    'social_django.context_processors.login_redirect',
                    'lib.middleware.sukima_settings_context_processors',
                ],
            },
        },
    ],
    'SITE_ID': 1,
    'DEBUG': False,
    'ROOT_URLCONF': '',
    'SECRET_KEY': 'not very secret in tests',
    'ELASTICINDEX_HOSTS': [{'host': '127.0.0.1', 'port': 9200}],
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
