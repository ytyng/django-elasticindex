ELASTICINDEX_HOSTS = [{'host': 'virgo.torico-tokyo.com', 'port': 9200}]


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': ' %(name)s %(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
    },
    'loggers': {
    }
}


def simple_console_log(log_name, level='DEBUG'):
    LOGGING['handlers'][log_name] = {
        'formatter': 'simple',
        'level': level,
        'class': 'logging.StreamHandler',
    }
    LOGGING['loggers'][log_name] = {
        'handlers': [log_name],
        'propagate': True,
        'level': level,
    }


simple_console_log('elasticsearch.trace', level='DEBUG')
simple_console_log('elasticsearch', level='DEBUG')
simple_console_log('elasticindex', level='DEBUG')
