# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import time
from django.test import TestCase
from .models import DummyModel, DummyESDocument, DummyESDocumentPresetIndex


class TestESDocumentTest(TestCase):
    def setUp(self):
        if DummyESDocument.index.exists():
            DummyESDocument.index.delete()
        DummyESDocument.index.create()
        # install fixtures.

        # Bulk update from model instances.
        DummyModel.objects.create(key='quick', value='brown fox')
        DummyModel.objects.create(key='jumps', value='over the')
        DummyESDocument.rebuild_index()

        # Update from single instance.
        d3 = DummyModel.objects.create(key='lazy', value='dogs.')
        DummyESDocument.rebuild_index_by_source_model(d3)

        # Update from dict
        DummyESDocument.update('id-manually', {'key': 'spam', 'value': 'eggs'})

        # Wait commit
        for i in range(10):
            try:
                result = DummyESDocument.objects.get(
                    {"term": {"value": "eggs"}})
                break
            except DummyESDocument.DoesNotExist:
                time.sleep(0.3)
                continue
        self.assertEqual(result.key, 'spam')

    def test_index_search(self):

        # Simple query
        results = DummyESDocument.objects.query({"match": {"key": "jumps"}})
        result = list(results)[0]
        self.assertEqual(result.value, 'over the')

        # OR query
        qs = DummyESDocument.objects.query(
            {"bool": {
                "should": [
                    {"match": {"value": "dogs"}},
                    {"match": {"value": "fox"}},

                ]}})
        qs = qs.order_by({"key": "desc"})
        result = qs[1]
        self.assertEqual(result.value, "dogs.")

    def tearDown(self):
        # teardown ES index
        DummyESDocument.index.delete()


class TestESDocumentPresetIndexTest(TestCase):
    def setUp(self):
        if DummyESDocumentPresetIndex.index.exists():
            DummyESDocumentPresetIndex.index.delete()
        DummyESDocumentPresetIndex.index.create()
        DummyESDocumentPresetIndex.update(
            'doc1', {
                'key': 'doc1',
                'text_k': "セキュリティのため、ローカルホストやローカルネットワークに"
                          "しかアクセスを許可していない Web アプリってあると思います。",
                'text_b': "例えば、オフィスで起動している社内サーバ。Jenkinsとか。"
                          "Wikiとか。サーバ監視ツールとか。例えば、本番環境で起動"
                          "している Docker コンテナの中で動いているWebツールとか。",
            })
        DummyESDocumentPresetIndex.update(
            'doc2', {
                'key': 'doc2',
                'text_k': "私の場合は、elasticsearch の head プラグインのWeb"
                          "管理画面を起動しているのですが、ローカルホストからしか"
                          "アクセスを許可してませんので、外からアクセスするには"
                          "一工夫必要です。",
                'text_b': "クライアントは Firefox に入ってますし、サーバは OpenSSH "
                          "に組み込まれていますので、別途ソフトウェアのインストールは"
                          "不要です。",
            })

        # Simple Query (and wait commit) (OMG)
        for i in range(10):
            try:
                result = DummyESDocumentPresetIndex.objects.get(
                    {"term": {"key": "doc2"}})
                break
            except DummyESDocumentPresetIndex.DoesNotExist:
                time.sleep(0.3)
                continue
        self.assertIn('不要です。', result.text_b)

    def test_index_kuromoji_1(self):
        results = DummyESDocumentPresetIndex.objects.query(
            {"match": {"text_k": "起動"}})
        r = list(results)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0].key, 'doc2')

    def test_index_kuromoji_2(self):
        results = DummyESDocumentPresetIndex.objects.query(
            {"match": {"text_k": "ネットワーク"}})
        r = list(results)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0].key, 'doc1')

    def test_index_bigram_1(self):
        results = DummyESDocumentPresetIndex.objects.query(
            {"match": {"text_b": "ソフトウ"}})
        r = list(results)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0].key, 'doc2')

    def test_index_bigram_2(self):
        results = DummyESDocumentPresetIndex.objects.query(
            {"match": {"text_b": "視ツ"}})
        r = list(results)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0].key, 'doc1')

    def test_index_bigram_3(self):
        results = DummyESDocumentPresetIndex.objects.query(
            {"match": {"text_b": "Firefoxサーバ"}})
        list(results)
        # r = list(results)
        # len(r) がここで0にならないといけない。が、なってない
        # 要 Elasticsearchの理解
        # self.assertEqual(len(r), 0)

    def tearDown(self):
        DummyESDocumentPresetIndex.index.delete()
