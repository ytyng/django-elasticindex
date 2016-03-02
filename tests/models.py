from django.db import models
from elasticindex.models import ElasticDocument, ElasticDocumentField as F


class DummyModel(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    value = models.TextField()


class DummyESDocument(ElasticDocument):
    INDEX = "elasticindex_test"
    DOC_TYPE = "elasticindex_test_doc"
    ALLOW_KUROMOJI = False

    source_model = DummyModel

    key = F(mapping={"type": "string", "index": "not_analized"})
    value = F(mapping={"type": "string"})
