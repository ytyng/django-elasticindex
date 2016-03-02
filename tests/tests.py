# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.test import TestCase
from .models import DummyModel, DummyESDocument


class TestESDocumentTest(TestCase):
    def test_index_creation(self):
        # install fixtures.
        DummyModel.objects.create(key='quick', value='brown fox')
        DummyModel.objects.create(key='jumps', value='over the')

        DummyESDocument.rebuild_index()

        d3 = DummyModel.objects.create(key='lazy', value='dogs.')

        DummyESDocument.rebuild_index_by_source_model(d3)

        results = DummyESDocument.objects.query({"match": {"key": "jumps"}})

        result = list(results)[0]

        self.assertEqual(result.value, 'over the')

        qs = DummyESDocument.objects.query(
            {"bool": {
                "should": [
                    {"match": {"value": "dogs"}},
                    {"match": {"value": "fox"}},

                ]}})
        qs = qs.order_by({"key": "desc"})
        result = qs[1]
        self.assertEqual(result.value, "dogs.")

        # teardown ES index
        # DummyESDocument.index.delete()
