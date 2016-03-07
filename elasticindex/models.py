# -*- coding: utf-8 -*-
"""
Elasticsearch を Django のモデルっぽく使うクラス
"""
from __future__ import unicode_literals
import logging
from collections import OrderedDict
from .client import get_es_client
from .managers import ElasticDocumentMeta
from .fields import ElasticDocumentField

logger = logging.getLogger('elasticindex')


class ElasticDocument(object, metaclass=ElasticDocumentMeta):  # flake8: NOQA
    """
    Elasticsearch のドキュメントを司るクラス

    本クラスの、.index は ElasticIndexManager のインスタンスが付く。
    ESのインデックス作成や削除などができる
    """

    INDEX = "default_index"
    DOC_TYPE = "default_doc_type"
    # インデックス生成時の settings辞書
    INDEX_SETTINGS = None

    source_model = None  # インデックス生成元モデル

    class DoesNotExist(Exception):
        pass

    class ResultKeyError(Exception):
        pass

    @classmethod
    def _fields(cls):
        """
        クラスに定義されている ElasticDocumentField を、再帰的に探す

        dir() + getattr() でも同じ処理ができるが、そうすると
        @property を暴発させてしまうので vars() + __bases__ で。

        :return: このクラスの持つ JsonMasterField の一覧
            キーがフィールド名(変数名), 値が JsonMasterField のインスタンス
        :rtype: dict
        """
        _fields_dict = OrderedDict()
        for base_class in cls.__bases__:
            if hasattr(base_class, '_fields'):
                _fields_dict.update(base_class._fields())

        for name, value in vars(cls).items():
            if isinstance(value, ElasticDocumentField):
                value.contribute_to_class(cls, name)
                _fields_dict[name] = value
        return _fields_dict

    @classmethod
    def _cached_fields(cls):
        """
        _fields の取得をクラス変数にキャッシュする

        比較的重い処理なので。
        """
        if not hasattr(cls, '_fields_cache'):
            cls._fields_cache = cls._fields()
        return cls._fields_cache

    @classmethod
    def rebuild_index(cls, limit=None, offset=None,
                      filtering_func=None, bulk_size=1000, **kwargs):
        """
        インデックスを再生成する
        :param limit:
        :param offset:
        :param filtering_func:
        :return:
        """
        client = get_es_client()
        qs = cls.source_model.objects.all()
        if filtering_func is not None:
            qs = filtering_func(qs)
        if offset:
            qs = qs[offset:offset + limit]
        elif limit:
            qs = qs[:limit]

        if not bulk_size:
            # non bulk mode
            logger.debug('No bulk mode.')
            for source_model in qs:
                logger.debug('source_model: {}'.format(source_model))
                client.index(
                    cls.INDEX, cls.DOC_TYPE,
                    cls.data_dict_for_index(source_model),
                    id=cls.get_id_of_source_model(source_model),
                    **kwargs)
            return

        # bulk update
        def _get_bulk_body(qs):
            bulk_body = []
            for source_model in qs:
                logger.debug('source_model: {}'.format(source_model))
                bulk_body.append({'index': {
                    "_id": cls.get_id_of_source_model(source_model)}})
                bulk_body.append(cls.data_dict_for_index(source_model))
                if len(bulk_body) > bulk_size:
                    yield bulk_body
                    bulk_body = []
            if bulk_body:
                yield bulk_body

        for bulk_body in _get_bulk_body(qs):
            logger.debug('bulk updating.')
            # logger.debug('{}'.format(bulk_body))
            client.bulk(bulk_body, index=cls.INDEX, doc_type=cls.DOC_TYPE,
                        **kwargs)

    @classmethod
    def update_bulk(cls, bulk_body, **kwargs):
        """
        バルク更新
        :type bulk_body: list
        """
        client = get_es_client()
        client.bulk(bulk_body, index=cls.INDEX, doc_type=cls.DOC_TYPE,
                    **kwargs)

    @classmethod
    def update(cls, id, data_dict, **kwargs):
        """
        1レコードの更新 (insert/update)
        dict で直接内容を指定する
        通常はこれは使わず、rebuild_index もしくは rebuild_index_by_source_model を使う
        :type data_dict: dict
        """
        client = get_es_client()
        client.index(
            cls.INDEX, cls.DOC_TYPE,
            data_dict, id=id, **kwargs)

    @classmethod
    def rebuild_index_by_source_model(cls, source_model, **kwargs):
        """
        元モデルを1つ指定してインデックスを再生成
        :param source_model:
        :return:
        """
        cls.update(cls.get_id_of_source_model(source_model),
                   cls.data_dict_for_index(source_model), **kwargs)

    @classmethod
    def data_dict_for_index(cls, source_model):
        params = {}
        for name, field in cls._cached_fields().items():
            params[name] = field.get_value_for_index_of_source_model(
                source_model)
        return params

    @classmethod
    def get_id_of_source_model(self, source_model):
        return source_model.pk

    def __init__(self, es_result):
        """
        ES検索結果からインスタンスを起こす
        """
        self.es_result = es_result
        self.es_id = es_result['_id']
        self.es_score = es_result['_score']
        es_source = es_result['_source']

        for field_name, field in self._cached_fields().items():
            if field_name not in es_source:
                raise self.ResultKeyError(field_name)
            value = field.get_value_from_index_source_value(
                es_source[field_name])
            setattr(self, field_name, value)
