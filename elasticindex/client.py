"""
settings に ELASTICINDEX_AWS_IAM があれば、
IAM クレデンシャルで Amazon ES への接続を行う
"""

import elasticsearch
from django.conf import settings

DEFAULT_TIMEOUT = 10


def get_es_client(*, timeout=DEFAULT_TIMEOUT):
    """
    :return: Elasticsearch
    :rtype: Elasticsearch
    """
    if getattr(settings, 'ELASTICINDEX_AWS_IAM', None):
        return _get_es_client_aws(timeout=timeout)
    return elasticsearch.Elasticsearch(
        settings.ELASTICINDEX_HOSTS, timeout=timeout
    )


def _get_es_client_aws(*, timeout=DEFAULT_TIMEOUT):
    """
    IAM を使って、Amazon ES にアクセスする場合
    :rtype: Elasticsearch
    """
    from requests_aws4auth import AWS4Auth

    iam = settings.ELASTICINDEX_AWS_IAM

    service_name = 'es'
    if settings.ELASTICINDEX_HOSTS:
        # OpenSearch Serverless の場合
        if (
            settings.ELASTICINDEX_HOSTS[0]
            .get('host', '')
            .endswith('.aoss.amazonaws.com')
        ):
            service_name = 'aoss'

    awsauth = AWS4Auth(
        iam['access_id'], iam['secret_key'], iam['region'], service_name
    )

    return elasticsearch.Elasticsearch(
        hosts=settings.ELASTICINDEX_HOSTS,
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=elasticsearch.connection.RequestsHttpConnection,
        timeout=timeout,
    )
