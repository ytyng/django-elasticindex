"""
settings に ELASTICINDEX_AWS_IAM があれば、
IAM クレデンシャルで Amazon ES への接続を行う
"""

import elasticsearch
from django.conf import settings


def get_es_client():
    """
    :return: Elasticsearch
    :rtype: Elasticsearch
    """
    if getattr(settings, 'ELASTICINDEX_AWS_IAM', None):
        return _get_es_client_aws()
    return elasticsearch.Elasticsearch(settings.ELASTICINDEX_HOSTS)


def _get_es_client_aws():
    """
    IAM を使って、Amazon ES にアクセスする場合
    :rtype: Elasticsearch
    """
    from requests_aws4auth import AWS4Auth
    iam = settings.ELASTICINDEX_AWS_IAM
    awsauth = AWS4Auth(
        iam['access_id'],
        iam['secret_key'],
        iam['region'],
        'es')

    return elasticsearch.Elasticsearch(
        hosts=settings.ELASTICINDEX_HOSTS,
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=elasticsearch.connection.RequestsHttpConnection
    )
