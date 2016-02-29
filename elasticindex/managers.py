# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import logging
import time
from collections import OrderedDict
from contextlib import contextmanager

import six
from django.utils.functional import cached_property

from .client import get_es_client

logger = logging.getLogger('elasticindex')


class ElasticQuerySet(object):
    def __init__(self, model_cls, body=None, params=None):
        self.model_cls = model_cls
        self.body = body or {"query": {"match_all": {}}}
        self.params = params or {}
        self.latest_total_count = None
        self.latest_raw_result = None
        self.query_finished = False

    def __len__(self):
        return len(self.result_list)

    def __iter__(self):
        return iter(self.result_list)

    def __bool__(self):
        return bool(self.result_list)

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if not isinstance(k, (slice,) + six.integer_types):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0)) or
                (isinstance(k, slice) and (k.start is None or k.start >= 0) and
                 (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."

        if self.query_finished:
            return self.result_list[k]

        if isinstance(k, slice):
            qs = self
            offset = 0
            if k.start is not None:
                offset = int(k.start)
                qs = qs.offset(offset)
            if k.stop is not None:
                limit = int(k.stop) - offset
                qs = qs.limit(limit)
            return list(qs)[::k.step] if k.step else qs

        qs = self.limit(1).offset(k)
        return list(qs)[0]

    def _clone(self):
        """
        :rtype: ElasticQuerySet
        """
        qs = self.__class__(
            self.model_cls, copy.deepcopy(self.body),
            copy.deepcopy(self.params))
        return qs

    @cached_property
    def result_list(self):
        self.query_finished = True
        return list(self.get_result())

    def get_result(self):
        """
        elasticsearch の search をそのまま実行
        :rtype: generator
        """
        with self.log_query():
            if self.params is not None:
                result = self.es_client.search(
                    index=self.model_cls.INDEX,
                    doc_type=self.model_cls.DOC_TYPE,
                    body=self.body, params=self.params)
            else:
                result = self.es_client.search(
                    index=self.model_cls.INDEX,
                    doc_type=self.model_cls.DOC_TYPE,
                    body=self.body)

        self.latest_total_count = result['hits']['total']
        self.latest_raw_result = result
        for hit in result['hits']['hits']:
            yield self.model_cls(hit)

    @cached_property
    def es_client(self):
        """
        :rtype: Elasticsearch
        """
        return get_es_client()

    def get_by_id(self, id):
        """
        Elasticsearch のIDで1件取得
        :param id:
        :return:
        """
        result = self.es_client.get(
            self.model_cls.INDEX, id, doc_type=self.model_cls.DOC_TYPE)
        self.latest_raw_result = result
        if not result['found']:
            raise self.model_cls.DoesNotExist(id)
        return self.model_cls(result)

    def delete_by_id(self, id):
        """
        Elasticsearch のIDで1件削除
        :param id: elasticsearch document id
        """
        result = self.es_client.delete(
            self.model_cls.INDEX, self.model_cls.DOC_TYPE, id)
        self.latest_raw_result = result
        return result

    def all(self):
        """
        :rtype: ElasticQuerySet
        """
        return self._clone()

    def limit(self, limit):
        """
        :rtype: ElasticQuerySet
        """
        o = self._clone()
        if limit is None:
            if 'size' in o.body:
                del o.body['size']
        else:
            o.body['size'] = limit
        return o

    def offset(self, offset):
        """
        :rtype: ElasticQuerySet
        """
        o = self._clone()
        if offset is None:
            if 'from' in o.body:
                del o.body['from']
        else:
            o.body['from'] = offset
        return o

    def query(self, filter_query_dict):
        """
        :param filter_query_dict:
          - {"match": {"product_id": 192}}
          - {"match_all": {}}  # default
          - {"multi_match": {
                "query": query_word,
                "fields": [
                    "upc", "title^3", "description", "authors",
                    "publishers", "tags", "keywords"]
            }}
          - {"bool": {
              "must": [
                {"match": {"is_used": True}},
                {"range": {"stock": {"gt": 0}}}
            ]}}

        :rtype: ElasticQuerySet
        """
        o = self._clone()
        o.body['query'] = filter_query_dict
        return o

    def set_body(self, body_dict):
        """
        replace query body
        """
        o = self._clone()
        o.body = body_dict
        return o

    def get(self, filter_query_dict):
        """
        1件取得
        複数件あってもエラーは出さず、黙って1件だけ返す
        """
        qs = self.query(filter_query_dict).limit(1)
        if not qs:
            raise self.model_cls.DoesNotExist(filter_query_dict)
        return qs[0]

    def count(self):
        """
        件数取得
        """
        if self.query_finished:
            return len(self.result_list)

        body = self.body.copy()
        if 'sort' in body:
            del body['sort']

        with self.log_query(label='count', body=body):
            if self.params is not None:
                result = self.es_client.count(
                    index=self.model_cls.INDEX,
                    doc_type=self.model_cls.DOC_TYPE,
                    body=body, params=self.params
                )
            else:
                result = self.es_client.count(
                    index=self.model_cls.INDEX,
                    doc_type=self.model_cls.DOC_TYPE,
                    body=body
                )
        self.latest_raw_result = result
        return result['count']

    def order_by(self, order_query_list):
        """
        sort パラメータをつける
        :type order_query_list: list, dict, string
        - "mz_score"
        - {"mz_score": "desc"}

        """
        o = self._clone()
        o.body['sort'] = order_query_list
        return o

    @property
    def log_query(self):
        """
        クエリをロギングするコンテクストマネージャ
        elasticsearch や elasticsearch.trace のロガーを
        DEBUG レベルで設定するともっと詳しく出る (結果が全部出る)
        """

        @contextmanager
        def _context(label='', body=None):
            start_time = time.time()
            yield
            elapsed_time = time.time() - start_time
            logger.debug('{}time:{}ms, body:{}'.format(
                '{}: '.format(label) if label else '',
                int(elapsed_time * 100), body or self.body))

        return _context

    def bulk(self, body):
        return self.es_client.bulk(
            body, index=self.model_cls.INDEX,
            doc_type=self.model_cls.DOC_TYPE)


class ElasticDocumentManager(object):
    """
    class ElasticDocumentManager(ElasticQuerySet)
    でもいいんだけど、インスタンス変数が汚れる可能性があるので
    クラスプロパティっぽい感じで、アクセスされるたびに新しいクエリセットを作ることにした
    """

    def __init__(self, model_cls, body=None, params=None):
        self.model_cls = model_cls

    def __get__(self, cls, owner):
        return ElasticQuerySet(self.model_cls)


class ElasticIndexManager(object):
    def __init__(self, model_cls):
        self.model_cls = model_cls

    @cached_property
    def mappings_properties(self):
        return OrderedDict(
            [
                (f_name, f.mapping)
                for f_name, f
                in self.model_cls._cached_fields().items()
                ])

    @cached_property
    def mappings(self):
        """
        インデックスの mappings の指定にそのまま使える dict
        """
        return {
            self.model_cls.DOC_TYPE: {
                "properties": self.mappings_properties
            }
        }

    def delete(self):
        """
        インデックスを削除
        :return:
        """
        es = get_es_client()
        es.indices.delete(self.model_cls.INDEX, ignore=[404, ])

    @cached_property
    def create_body_params(self):
        body = {"mappings": self.mappings}
        if self.model_cls.ALLOW_KUROMOJI:
            body["settings"] = {
                "index": {
                    "analysis": {
                        "tokenizer": {
                            "kuromoji": {
                                "type": "kuromoji_tokenizer"
                            }
                        },
                        "analyzer": {
                            "analyzer": {
                                "type": "custom",
                                "tokenizer": "kuromoji"
                            }
                        }
                    }
                },
            }
        return body

    def create(self):
        """
        インデックスを作成
        :return:
        """
        es = get_es_client()
        es.indices.create(
            self.model_cls.INDEX, self.create_body_params)

    def exists(self):
        """
        インデックスが存在するか
        """
        es = get_es_client()
        return es.indices.exists(self.model_cls.INDEX)


class ElasticDocumentMeta(type):
    def __new__(mcs, name, bases, attrs):
        c = super(ElasticDocumentMeta, mcs).__new__(
            mcs, name, bases, attrs)

        c.objects = ElasticDocumentManager(c)
        c.index = ElasticIndexManager(c)
        return c
