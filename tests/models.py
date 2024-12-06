from django.db import models

from elasticindex.models import ElasticDocument
from elasticindex.models import ElasticDocumentField as F


class DummyModel(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    value = models.TextField()


class DummyESDocument(ElasticDocument):
    INDEX = "elasticindex_test_index"

    source_model = DummyModel

    key = F(mapping={"type": "keyword"})
    value = F(mapping={"type": "text"})


class DummyESDocumentPresetIndex(ElasticDocument):
    INDEX = "elasticindex_test_index_preset_i"

    INDEX_SETTINGS = {
        "analysis": {
            "analyzer": {
                "standard_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                },
                "bigram_analyzer": {
                    "type": "custom",
                    "tokenizer": "bigram",
                },
            },
            "tokenizer": {
                "standard": {
                    "type": "standard",
                    "max_token_length": 5,
                },
                "bigram": {
                    "type": "ngram",
                    "min_gram": "2",
                    "max_gram": "2",
                    "token_chars": [
                        "letter",
                        "digit",
                    ],
                },
            },
        },
    }

    key = F(mapping={"type": "keyword"})
    text_s = F(
        mapping={
            "type": "text",
            "analyzer": "standard_analyzer",
        }
    )
    text_b = F(
        mapping={
            "type": "text",
            "analyzer": "bigram_analyzer",
        }
    )
