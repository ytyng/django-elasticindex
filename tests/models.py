from django.db import models
from elasticindex.models import ElasticDocument, ElasticDocumentField as F


class DummyModel(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    value = models.TextField()


class DummyESDocument(ElasticDocument):
    INDEX = "elasticindex_test_index"
    DOC_TYPE = "elasticindex_test_doc"

    source_model = DummyModel

    key = F(mapping={"type": "string", "index": "not_analyzed"})
    value = F(mapping={"type": "string"})


class DummyESDocumentPresetIndex(ElasticDocument):
    INDEX = "elasticindex_test_index_preset_i"
    DOC_TYPE = "elasticindex_test_doc_preset_i"

    INDEX_SETTINGS = {
        "index": {
            "analysis": {
                "tokenizer": {
                    "kuromoji": {
                        "type": "kuromoji_tokenizer"
                    },
                    "bigram": {
                        "type": "nGram",
                        "min_gram": "2",
                        "max_gram": "2",
                        "token_chars": [
                            "letter",
                            "digit"
                        ]},
                },
                "analyzer": {
                    "kuromoji_analyzer": {
                        "type": "custom",
                        "tokenizer": "kuromoji_tokenizer"
                    },
                    "bigram_analyzer": {
                        "type": "custom",
                        "tokenizer": "bigram"
                    }
                }
            }
        },
    }

    key = F(mapping={"type": "string", "index": "not_analyzed"})
    text_k = F(mapping={
        "type": "string",
        "analyzer": "kuromoji_analyzer",
    })
    text_b = F(mapping={
        "type": "string",
        "tokenizer": "bigram",
        "analyzer": "bigram_analyzer",
    })
